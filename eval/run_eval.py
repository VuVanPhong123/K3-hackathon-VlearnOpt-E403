from __future__ import annotations

import asyncio
import inspect
import json
import logging
import sys
import tempfile
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "be"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BE))

from app.config import settings
from app.schemas import ChatRequestV2, PageContextResponse
from app.services.answer_service import AnswerService
from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.orchestration_service import OrchestrationService
from app.services.provider_gateway import ProviderGateway
from app.services.providers.base import (
    ProviderRequestError,
    ProviderResult,
    ProviderTemporaryError,
)
from app.services.retrieval_service import RetrievalService
from eval.scorers import score_case

QUALITY_BAR = {
    "overall_case_pass_rate": 0.90,
    "status_accuracy": 1.00,
    "mode_accuracy": 0.95,
    "page_context_accuracy": 0.95,
    "citation_accuracy": 0.95,
    "provider_invocation_accuracy": 1.00,
    "media_path_accuracy": 1.00,
    "fallback_accuracy": 1.00,
    "prompt_context_accuracy": 0.95,
    "history_limit_accuracy": 1.00,
    "utf8_response_accuracy": 1.00,
    "error_detail_accuracy": 1.00,
    "decision_accuracy": 1.00,
    "clarification_accuracy": 1.00,
    "abstention_accuracy": 1.00,
    "no_crash_rate": 1.00,
}

PAGE_TEXTS = {
    1: "RAG giúp trợ lý trả lời dựa trên bằng chứng tài liệu và trả citation theo trang.",
    2: (
        "Selected text is the strongest local context. "
        "A visual region carries an exact image crop. "
        "An attached page includes text and the full page image."
    ),
    3: (
        "Figure 1: Encoder-decoder architecture. "
        "Input tokens flow through attention before output generation."
    ),
    4: (
        "Scaled dot-product attention dùng công thức "
        "Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V. "
        "Hệ số scale kiểm soát tích vô hướng lớn trước softmax."
    ),
    5: (
        "Multi-head attention dùng nhiều attention head để học các quan hệ bổ sung. "
        "Đầu ra được nối lại rồi chiếu tuyến tính."
    ),
    6: (
        "Table 1 so sánh self-attention, recurrent và convolutional theo complexity, "
        "sequential operations và maximum path length."
    ),
    7: (
        "Training loss chart cho thấy loss giảm dần khi số training step tăng. "
        "Đường biểu diễn đi xuống ổn định."
    ),
    8: "Visual-only attention map gồm một ma trận màu, gần như không có văn bản.",
    9: (
        "Kết luận: trợ lý grounded cần nói rõ khi thiếu bằng chứng "
        "thay vì tự bịa nội dung."
    ),
}


def load_cases(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _fixture_chunks() -> list[dict]:
    provider = HashEmbeddingProvider()
    texts = [PAGE_TEXTS[page] for page in sorted(PAGE_TEXTS)]
    vectors = provider.embed_passages(texts)
    return [
        {
            "chunk_id": f"fixture-page-{page}",
            "document_id": "fixture",
            "page_number": page,
            "heading": PAGE_TEXTS[page].split(".", 1)[0],
            "text": PAGE_TEXTS[page],
            "embedding": vector,
        }
        for page, vector in zip(sorted(PAGE_TEXTS), vectors)
    ]


class FixtureDocumentRepository:
    def list_pages(self, document_id: str) -> list[dict]:
        return [
            {"page_number": page, "raw_text": text}
            for page, text in PAGE_TEXTS.items()
        ]


class FixtureDocumentService:
    def __init__(self) -> None:
        self.repository = FixtureDocumentRepository()
        self.metadata = SimpleNamespace(
            id="fixture",
            original_filename="tài-liệu-đánh-giá.pdf",
            page_count=len(PAGE_TEXTS),
            version=1,
            status="READY",
        )

    def get_metadata(self, document_id: str):
        if document_id != "fixture":
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
        return self.metadata


class FixturePageContextService:
    def get_page_text(self, document_id: str, page_number: int) -> PageContextResponse:
        if document_id != "fixture" or page_number not in PAGE_TEXTS:
            raise HTTPException(status_code=400, detail="Trang PDF không hợp lệ.")
        text = PAGE_TEXTS[page_number]
        return PageContextResponse(
            document_id=document_id,
            page_number=page_number,
            text=text,
            has_text=bool(text),
        )


class FixtureVisualContextService:
    def __init__(self, directory: Path) -> None:
        self.image_path = directory / "fixture-page.png"
        self.image_path.write_bytes(b"\x89PNG\r\n\x1a\nfixture-image")

    def render_page(self, document_id: str, page_number: int) -> Path:
        return self.image_path

    def render_crop(self, document_id: str, page_number: int, bbox) -> Path:
        return self.image_path

    def get_overlapping_text(self, document_id: str, page_number: int, bbox) -> str:
        return PAGE_TEXTS.get(page_number, "")


class FixtureChunkRepository:
    def __init__(self) -> None:
        self.chunks = _fixture_chunks()

    def list_chunks(self, document_id: str) -> list[dict]:
        return self.chunks if document_id == "fixture" else []


class NullConversationRepository:
    def ensure_conversation(self, *args, **kwargs) -> None:
        pass

    def add_message(self, *args, **kwargs) -> None:
        pass


class RecordingProvider:
    def __init__(
        self,
        name: str,
        calls: list[dict],
        errors: dict[str, str],
    ) -> None:
        self.name = name
        self.calls = calls
        self.errors = errors

    def _record(self, kind: str, payload: str, history_count: int, image_attached: bool) -> None:
        self.calls.append(
            {
                "provider": self.name,
                "kind": kind,
                "payload": payload,
                "history_count": history_count,
                "image_attached": image_attached,
            }
        )
        error = self.errors.get(f"{self.name}_{kind}")
        if error == "temporary":
            raise ProviderTemporaryError("Lỗi tạm thời từ provider giả.")
        if error == "request":
            raise ProviderRequestError("Yêu cầu không hợp lệ từ provider giả.")

    async def generate(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, str]],
    ) -> ProviderResult:
        payload = system_prompt + "\n" + "\n".join(item["content"] for item in messages)
        self._record("text", payload, max(0, len(messages) - 1), False)
        return ProviderResult(
            text=f"Câu trả lời tiếng Việt từ {self.name}.",
            provider=self.name,
            model=f"fake-{self.name}-text",
        )

    async def generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResult:
        self._record(
            "multimodal",
            system_prompt + "\n" + text_prompt,
            len(history or []),
            bool(image_bytes),
        )
        return ProviderResult(
            text=f"Câu trả lời tiếng Việt từ {self.name}.",
            provider=self.name,
            model=f"fake-{self.name}-multimodal",
        )


def build_request(payload: dict) -> ChatRequestV2:
    return ChatRequestV2.model_validate(payload)


def _configure_case(case: dict) -> dict[str, object]:
    original = {
        "openai_api_key": settings.openai_api_key,
        "gemini_api_key": settings.gemini_api_key,
        "primary_text_provider": settings.primary_text_provider,
        "fallback_text_provider": settings.fallback_text_provider,
        "vision_primary_provider": settings.vision_primary_provider,
        "vision_fallback_provider": settings.vision_fallback_provider,
        "enable_gemini_fallback": settings.enable_gemini_fallback,
        "enable_reranker": settings.enable_reranker,
    }
    scenario = case.get("scenario") or {}
    credentials = scenario.get("credentials", "both")
    settings.openai_api_key = "" if credentials == "none" else "eval-openai"
    settings.gemini_api_key = "" if credentials == "none" else "eval-gemini"
    settings.primary_text_provider = "openai"
    settings.fallback_text_provider = "gemini"
    settings.vision_primary_provider = "gemini"
    settings.vision_fallback_provider = "openai"
    settings.enable_gemini_fallback = True
    settings.enable_reranker = False
    return original


def _restore_settings(original: dict[str, object]) -> None:
    for key, value in original.items():
        setattr(settings, key, value)


def _has_vietnamese_diacritics(value: str) -> bool:
    return any(character in value for character in "ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ")


async def predict(case: dict, temp_dir: Path) -> dict:
    calls: list[dict] = []
    errors = (case.get("scenario") or {}).get("provider_errors") or {}
    openai = RecordingProvider("openai", calls, errors)
    gemini = RecordingProvider("gemini", calls, errors)
    gateway = ProviderGateway(
        openai_factory=lambda: openai,
        gemini_factory=lambda: gemini,
    )
    document_service = FixtureDocumentService()
    retrieval = RetrievalService(
        FixtureChunkRepository(),
        EmbeddingService(HashEmbeddingProvider()),
    )
    service = OrchestrationService(
        answer_service=AnswerService(gateway),
        document_service=document_service,
        page_context_service=FixturePageContextService(),
        visual_context_service=FixtureVisualContextService(temp_dir),
        retrieval_service=retrieval,
        conversation_repository=NullConversationRepository(),
    )
    original_settings = _configure_case(case)
    try:
        request = build_request(case["input"])
        response = await service.chat(request)
        answer = response.answer
        return {
            "status_code": 200,
            "mode": response.trace.intent,
            "decision": response.trace.decision,
            "needs_clarification": response.needs_clarification,
            "abstained": response.abstained,
            "pages_used": response.trace.pages_used,
            "citation_pages": [
                citation.page_number
                for citation in response.citations
                if citation.page_number is not None
            ],
            "provider": response.provider,
            "fallback_used": response.fallback_used,
            "image_used": response.trace.image_used,
            "answer": answer,
            "answer_has_vietnamese_diacritics": _has_vietnamese_diacritics(answer),
            "provider_calls": calls,
            "provider_called": bool(calls),
            "call_kinds": [item["kind"] for item in calls],
            "attempted_providers": [item["provider"] for item in calls],
            "provider_inputs": [item["payload"] for item in calls],
            "max_history_count": max(
                (item["history_count"] for item in calls),
                default=0,
            ),
            "all_images_attached": all(
                item["image_attached"]
                for item in calls
                if item["kind"] == "multimodal"
            ),
            "no_crash": True,
        }
    except HTTPException as exc:
        return {
            "status_code": exc.status_code,
            "error": str(exc.detail),
            "mode": None,
            "decision": None,
            "needs_clarification": False,
            "abstained": False,
            "pages_used": [],
            "citation_pages": [],
            "provider": None,
            "fallback_used": False,
            "image_used": False,
            "answer": "",
            "answer_has_vietnamese_diacritics": _has_vietnamese_diacritics(str(exc.detail)),
            "provider_calls": calls,
            "provider_called": bool(calls),
            "call_kinds": [item["kind"] for item in calls],
            "attempted_providers": [item["provider"] for item in calls],
            "provider_inputs": [item["payload"] for item in calls],
            "max_history_count": max(
                (item["history_count"] for item in calls),
                default=0,
            ),
            "all_images_attached": all(
                item["image_attached"]
                for item in calls
                if item["kind"] == "multimodal"
            ),
            "no_crash": True,
        }
    except Exception as exc:
        return {
            "status_code": 500,
            "error": f"{type(exc).__name__}: {exc}",
            "mode": None,
            "decision": None,
            "needs_clarification": False,
            "abstained": False,
            "pages_used": [],
            "citation_pages": [],
            "provider_calls": calls,
            "provider_called": bool(calls),
            "no_crash": False,
        }
    finally:
        _restore_settings(original_settings)


def aggregate(results: list[dict]) -> dict:
    metrics: dict[str, float | int | dict] = {
        "cases": len(results),
        "categories": dict(Counter(item["case"]["category"] for item in results)),
    }
    score_to_metric = {
        "status": "status_accuracy",
        "mode": "mode_accuracy",
        "page_context": "page_context_accuracy",
        "citation": "citation_accuracy",
        "provider_invocation": "provider_invocation_accuracy",
        "media_path": "media_path_accuracy",
        "fallback": "fallback_accuracy",
        "prompt_context": "prompt_context_accuracy",
        "history_limit": "history_limit_accuracy",
        "utf8_response": "utf8_response_accuracy",
        "error_detail": "error_detail_accuracy",
        "decision": "decision_accuracy",
        "clarification": "clarification_accuracy",
        "abstention": "abstention_accuracy",
        "no_crash": "no_crash_rate",
    }
    for score_name, metric_name in score_to_metric.items():
        applicable = [
            item["scores"][score_name]
            for item in results
            if item["scores"][score_name] is not None
        ]
        metrics[metric_name] = (
            sum(value is True for value in applicable) / len(applicable)
            if applicable
            else 1.0
        )
    metrics["overall_case_pass_rate"] = (
        sum(item["scores"]["passed"] for item in results) / len(results)
        if results
        else 0.0
    )
    return metrics


def _assert_prediction_independence() -> None:
    source = inspect.getsource(predict)
    if '["expected"]' in source or ".get(\"expected\"" in source:
        raise RuntimeError("Hàm predict không được đọc expected.")


async def main() -> int:
    logging.getLogger("app.services.provider_gateway").setLevel(logging.CRITICAL)
    _assert_prediction_independence()
    cases = load_cases(ROOT / "eval" / "golden_set.jsonl")
    if len(cases) < 31:
        raise RuntimeError("Golden set không được giảm xuống dưới 31 case.")

    results = []
    with tempfile.TemporaryDirectory(prefix="vlearn-eval-") as directory:
        temp_dir = Path(directory)
        for case in cases:
            prediction = await predict(case, temp_dir)
            scores = score_case(case, prediction)
            results.append(
                {
                    "case_id": case["case_id"],
                    "case": case,
                    "prediction": prediction,
                    "scores": scores,
                }
            )

    metrics = aggregate(results)
    quality_bar_passed = all(
        metrics[metric] >= threshold
        for metric, threshold in QUALITY_BAR.items()
    )
    report = {
        "quality_bar": QUALITY_BAR,
        "quality_bar_passed": quality_bar_passed,
        "metrics": metrics,
        "failed_cases": [
            item["case_id"]
            for item in results
            if not item["scores"]["passed"]
        ],
        "results": results,
    }
    output = ROOT / "eval" / "results" / "latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "cases": len(cases),
                "quality_bar_passed": quality_bar_passed,
                "metrics": metrics,
                "failed_cases": report["failed_cases"],
                "report": str(output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if quality_bar_passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
