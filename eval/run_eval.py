from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import logging
import sys
import tempfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "codebase" / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BE))

from app.config import settings
from app.schemas import ChatRequestV2
from app.services.answer_service import AnswerService
from app.services.embedding_service import EmbeddingService
from app.services.orchestration_service import OrchestrationService
from app.services.provider_gateway import ProviderGateway
from app.services.providers.base import (
    ProviderRequestError,
    ProviderResult,
    ProviderTemporaryError,
)
from app.services.retrieval_service import RetrievalService
from eval.pdf_eval_fixture import DEFAULT_DOCUMENT_ID, PdfEvalFixture
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
    "no_crash_rate": 1.00,
}

CATEGORY_COUNTS = {
    "page_chat": 11,
    "general_chat": 6,
    "text_selection": 4,
    "validation": 4,
    "document_search": 4,
    "visual_region": 3,
    "document_visual_search": 3,
    "context_priority": 2,
    "provider_fallback": 2,
    "provider_error": 2,
    "history": 1,
    "localization": 1,
}


def load_cases(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


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
        self.calls[-1]["image_byte_length"] = len(image_bytes)
        self.calls[-1]["image_sha256"] = hashlib.sha256(image_bytes).hexdigest() if image_bytes else ""
        self.calls[-1]["mime_type"] = mime_type
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


async def predict(case: dict, fixture: PdfEvalFixture) -> dict:
    calls: list[dict] = []
    errors = (case.get("scenario") or {}).get("provider_errors") or {}
    openai = RecordingProvider("openai", calls, errors)
    gemini = RecordingProvider("gemini", calls, errors)
    gateway = ProviderGateway(
        openai_factory=lambda: openai,
        gemini_factory=lambda: gemini,
    )
    retrieval = RetrievalService(
        fixture.chunk_repository,
        EmbeddingService(fixture.embedding_provider),
    )
    service = OrchestrationService(
        answer_service=AnswerService(gateway),
        document_service=fixture.document_service,
        page_context_service=fixture.page_context_service,
        visual_context_service=fixture.visual_context_service,
        retrieval_service=retrieval,
        conversation_repository=NullConversationRepository(),
    )
    original_settings = _configure_case(case)
    visual_start = len(fixture.visual_context_service.diagnostics)
    try:
        request = build_request(case["input"])
        response = await service.chat(request)
        answer = response.answer
        return {
            "status_code": 200,
            "mode": response.trace.intent,
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
            "image_byte_lengths": [
                item["image_byte_length"]
                for item in calls
                if item.get("image_byte_length") is not None
            ],
            "image_sha256s": [
                item["image_sha256"]
                for item in calls
                if item.get("image_sha256")
            ],
            "visual_diagnostics": fixture.visual_context_service.diagnostics[visual_start:],
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
            "image_byte_lengths": [
                item["image_byte_length"]
                for item in calls
                if item.get("image_byte_length") is not None
            ],
            "image_sha256s": [
                item["image_sha256"]
                for item in calls
                if item.get("image_sha256")
            ],
            "visual_diagnostics": fixture.visual_context_service.diagnostics[visual_start:],
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
            "pages_used": [],
            "citation_pages": [],
            "provider_calls": calls,
            "provider_called": bool(calls),
            "visual_diagnostics": fixture.visual_context_service.diagnostics[visual_start:],
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the VLearn Tutor golden eval against a real PDF.")
    parser.add_argument(
        "--document",
        type=Path,
        default=None,
        help="Path to d2-slide-hackathon.pdf. Defaults to eval/fixtures/d2-slide-hackathon.pdf if present.",
    )
    return parser.parse_args()


def _resolve_document_path(path: Path | None) -> Path:
    default = ROOT / "eval" / "fixtures" / "d2-slide-hackathon.pdf"
    document = path or default
    if not document.exists():
        raise FileNotFoundError(
            "Không tìm thấy PDF eval. Truyền rõ --document \"path/to/d2-slide-hackathon.pdf\"; "
            "runner không còn fallback sang fixture text giả."
        )
    return document


def _assert_case_contract(cases: list[dict]) -> None:
    if len(cases) != 43:
        raise RuntimeError(f"Golden set phải có đúng 43 case, hiện có {len(cases)}.")
    counts = Counter(item["category"] for item in cases)
    if dict(counts) != CATEGORY_COUNTS:
        raise RuntimeError(f"Phân bổ category sai: {dict(counts)}")


async def main() -> int:
    logging.getLogger("app.services.provider_gateway").setLevel(logging.CRITICAL)
    args = _parse_args()
    _assert_prediction_independence()
    cases = load_cases(ROOT / "eval" / "golden_set.jsonl")
    _assert_case_contract(cases)

    results = []
    with tempfile.TemporaryDirectory(prefix="vlearn-eval-") as directory:
        temp_dir = Path(directory)
        fixture = PdfEvalFixture.from_pdf(
            _resolve_document_path(args.document),
            temp_dir,
            document_id=DEFAULT_DOCUMENT_ID,
        )
        for case in cases:
            prediction = await predict(case, fixture)
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
        "document": fixture.manifest,
        "generated_at": datetime.now(UTC).isoformat(),
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
                "document": fixture.manifest,
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
