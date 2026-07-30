from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.config import settings
from app.schemas import (
    BBox,
    ChatContextV2,
    ChatHistoryItem,
    ChatRequestV2,
    PageContextResponse,
    TextSelection,
    VisualRegion,
)
from app.services.answer_service import AnswerService
from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.orchestration_service import OrchestrationService
from app.services.page_context_service import PageContextService
from app.services.provider_gateway import ProviderGateway
from app.services.providers.base import (
    ProviderRequestError,
    ProviderResult,
    ProviderTemporaryError,
)
from app.services.retrieval_service import RetrievalResult, RetrievalService
from tests.fixtures import create_fixture_pdf


class FakeProvider:
    def __init__(self, *, text: str = "Câu trả lời từ mô hình.", error: Exception | None = None) -> None:
        self.text = text
        self.error = error
        self.calls: list[dict] = []

    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> ProviderResult:
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        if self.error:
            raise self.error
        return ProviderResult(text=self.text, provider="openai", model="fake-openai")

    async def generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResult:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": [*(history or []), {"role": "user", "content": text_prompt}],
                "image_bytes": image_bytes,
                "mime_type": mime_type,
            }
        )
        if self.error:
            raise self.error
        return ProviderResult(text=self.text, provider="openai", model="fake-openai-vision")


class FakeConversationRepository:
    def ensure_conversation(self, *args, **kwargs) -> None:
        pass

    def add_message(self, *args, **kwargs) -> None:
        pass


class FakeDocumentService:
    def __init__(self, *, status: str = "READY", page_count: int = 3) -> None:
        self.metadata = SimpleNamespace(
            id="doc-1",
            original_filename="bài-học.pdf",
            status=status,
            page_count=page_count,
        )
        self.calls = 0
        self.repository = SimpleNamespace(list_pages=lambda document_id: [])

    def get_metadata(self, document_id: str):
        self.calls += 1
        if document_id != "doc-1":
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
        return self.metadata


class FakePageContextService:
    def __init__(self, text: str = "Nội dung riêng của trang ba.") -> None:
        self.text = text
        self.calls: list[tuple[str, int]] = []

    def get_page_text(self, document_id: str, page_number: int) -> PageContextResponse:
        self.calls.append((document_id, page_number))
        return PageContextResponse(
            document_id=document_id,
            page_number=page_number,
            text=self.text,
            has_text=bool(self.text),
        )


class FakeVisualContextService:
    def __init__(self, tmp_path: Path) -> None:
        self.path = tmp_path / "page.png"
        self.path.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
        self.page_calls: list[tuple[str, int]] = []
        self.crop_calls: list[tuple[str, int, BBox]] = []

    def render_page(self, document_id: str, page_number: int) -> Path:
        self.page_calls.append((document_id, page_number))
        return self.path

    def render_crop(self, document_id: str, page_number: int, bbox) -> Path:
        self.crop_calls.append((document_id, page_number, bbox))
        return self.path

    def get_overlapping_text(self, document_id: str, page_number: int, bbox) -> str:
        return "Văn bản trong vùng."


class FakeRetrievalService:
    def __init__(self, results: list[RetrievalResult] | None = None) -> None:
        self.results = results or []
        self.calls: list[tuple[str, str, int]] = []

    def search(self, document_id: str, query: str, top_k: int):
        self.calls.append((document_id, query, top_k))
        return self.results


class InMemoryChunkRepository:
    def __init__(self, chunks: list[dict]) -> None:
        self.chunks = chunks

    def list_chunks(self, document_id: str) -> list[dict]:
        return self.chunks if document_id == "doc-1" else []


def build_term_retrieval(chunks: list[dict]) -> RetrievalService:
    provider = HashEmbeddingProvider()
    embedded = []
    vectors = provider.embed_passages([chunk["text"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        embedded.append({**chunk, "embedding": vector})
    return RetrievalService(InMemoryChunkRepository(embedded), EmbeddingService(provider))


def build_service(
    provider: FakeProvider,
    *,
    document_service: FakeDocumentService | None = None,
    page_service: FakePageContextService | None = None,
    tmp_path: Path | None = None,
    visual_service: FakeVisualContextService | None = None,
    retrieval_service: FakeRetrievalService | None = None,
) -> OrchestrationService:
    gateway = ProviderGateway(
        openai_factory=lambda: provider,
        gemini_factory=lambda: provider,
    )
    return OrchestrationService(
        answer_service=AnswerService(gateway),
        document_service=document_service or FakeDocumentService(),
        page_context_service=page_service or FakePageContextService(),
        visual_context_service=visual_service or (FakeVisualContextService(tmp_path) if tmp_path else None),
        retrieval_service=retrieval_service,
        conversation_repository=FakeConversationRepository(),
    )


@pytest.fixture(autouse=True)
def configured_openai(monkeypatch):
    monkeypatch.setattr(settings, "primary_text_provider", "openai")
    monkeypatch.setattr(settings, "fallback_text_provider", "gemini")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "enable_gemini_fallback", True)


@pytest.mark.asyncio
async def test_general_chat_calls_provider_without_document_or_citation() -> None:
    provider = FakeProvider()
    document_service = FakeDocumentService(status="PROCESSING")
    response = await build_service(provider, document_service=document_service).chat(
        ChatRequestV2(
            message="Hãy giúp tôi lập kế hoạch học tập.",
            document_id="doc-1",
            context=ChatContextV2(),
            history=[
                ChatHistoryItem(role="user", content=f"Tin nhắn {index}")
                for index in range(10)
            ],
            answer_mode="allow_general_knowledge",
        )
    )

    assert response.answer
    assert response.citations == []
    assert response.trace.intent == "GENERAL_CHAT"
    assert document_service.calls == 0
    assert len(provider.calls) == 1
    assert len(provider.calls[0]["messages"]) == 11


@pytest.mark.asyncio
async def test_page_chat_sends_exact_page_text_and_returns_page_citation(tmp_path: Path) -> None:
    provider = FakeProvider(text="Giải thích dựa trên trang ba.")
    page_service = FakePageContextService("Bằng chứng chỉ có ở trang ba.")
    response = await build_service(provider, page_service=page_service, tmp_path=tmp_path).chat(
        ChatRequestV2(
            message="Giải thích nội dung chính.",
            document_id="doc-1",
            context=ChatContextV2(attached_pages=[3]),
        )
    )

    assert page_service.calls == [("doc-1", 3)]
    assert "Bằng chứng chỉ có ở trang ba." in provider.calls[0]["messages"][-1]["content"]
    assert response.citations[0].page_number == 3
    assert response.trace.pages_used == [3]


@pytest.mark.asyncio
async def test_processing_document_page_chat_is_not_blocked(tmp_path: Path) -> None:
    provider = FakeProvider()
    response = await build_service(
        provider,
        document_service=FakeDocumentService(status="PROCESSING"),
        tmp_path=tmp_path,
    ).chat(
        ChatRequestV2(
            message="Trang này nói gì?",
            document_id="doc-1",
            context=ChatContextV2(attached_pages=[2]),
        )
    )

    assert response.trace.intent == "PAGE_CHAT"
    assert response.trace.provider == "openai"
    assert len(provider.calls) == 1


def test_page_context_reads_pdf_directly_when_page_is_not_indexed(tmp_path: Path) -> None:
    pdf_path = create_fixture_pdf(tmp_path / "fixture.pdf")

    class DirectDocumentService:
        def get_metadata(self, document_id: str):
            return SimpleNamespace(page_count=6)

        def get_file_path(self, document_id: str):
            return pdf_path

    class EmptyPageRepository:
        def get_page(self, document_id: str, page_number: int):
            return None

    service = PageContextService(DirectDocumentService())
    service.repository = EmptyPageRepository()
    result = service.get_page_text("doc-1", 2)

    assert result.page_number == 2
    assert result.has_text is True
    assert "Context priority" in result.text


@pytest.mark.asyncio
async def test_missing_api_key_returns_clear_503(monkeypatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "gemini_api_key", "")

    with pytest.raises(HTTPException) as error:
        await build_service(FakeProvider()).chat(
            ChatRequestV2(message="Xin chào", context=ChatContextV2())
        )

    assert error.value.status_code == 503
    assert error.value.detail == "Chưa cấu hình API key cho chatbot."


@pytest.mark.asyncio
async def test_invalid_page_returns_400() -> None:
    with pytest.raises(HTTPException) as error:
        await build_service(FakeProvider()).chat(
            ChatRequestV2(
                message="Trang này nói gì?",
                document_id="doc-1",
                context=ChatContextV2(attached_pages=[99]),
            )
        )

    assert error.value.status_code == 400


@pytest.mark.asyncio
async def test_provider_failure_does_not_return_fake_success() -> None:
    provider = FakeProvider(error=ProviderTemporaryError("timeout"))
    with pytest.raises(HTTPException) as error:
        await build_service(provider).chat(
            ChatRequestV2(message="Xin chào", context=ChatContextV2())
        )

    assert error.value.status_code == 503
    assert "tạm thời không khả dụng" in error.value.detail


@pytest.mark.asyncio
async def test_request_error_is_reported_without_fake_answer() -> None:
    provider = FakeProvider(error=ProviderRequestError("bad model"))
    with pytest.raises(HTTPException) as error:
        await build_service(provider).chat(
            ChatRequestV2(message="Xin chào", context=ChatContextV2())
        )

    assert error.value.status_code == 502


@pytest.mark.asyncio
async def test_utf8_answer_is_preserved() -> None:
    expected = "Mình sẽ hỗ trợ bạn học rõ ràng và có hệ thống."
    response = await build_service(FakeProvider(text=expected)).chat(
        ChatRequestV2(message="Xin chào", context=ChatContextV2())
    )
    assert response.answer == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("message", "expected_page"),
    [
        ("Giải thích nội dung trang 5", 5),
        ("Giải thích bảng so sánh ở slide 6", 6),
        ("Nội dung ở page 4 là gì?", 4),
        ("Giải thích p. 2", 2),
    ],
)
async def test_explicit_page_queries_use_page_image(
    tmp_path: Path,
    message: str,
    expected_page: int,
) -> None:
    provider = FakeProvider()
    visual = FakeVisualContextService(tmp_path)
    response = await build_service(
        provider,
        document_service=FakeDocumentService(page_count=8),
        visual_service=visual,
    ).chat(
        ChatRequestV2(
            message=message,
            document_id="doc-1",
            context=ChatContextV2(active_page=1),
        )
    )

    assert response.trace.intent == "PAGE_CHAT"
    assert response.trace.image_used is True
    assert visual.page_calls == [("doc-1", expected_page)]
    assert provider.calls[0]["image_bytes"]
    assert response.citations[0].page_number == expected_page


@pytest.mark.asyncio
async def test_current_page_query_uses_active_page(tmp_path: Path) -> None:
    response = await build_service(
        FakeProvider(),
        document_service=FakeDocumentService(page_count=8),
        tmp_path=tmp_path,
    ).chat(
        ChatRequestV2(
            message="Giải thích bảng này",
            document_id="doc-1",
            context=ChatContextV2(active_page=6),
        )
    )
    assert response.trace.pages_used == [6]


@pytest.mark.asyncio
async def test_valid_text_selection_is_sent_with_surrounding_context() -> None:
    provider = FakeProvider()
    page_text = "Đoạn mở đầu. Cơ chế attention cho phép mô hình tập trung vào token liên quan. Đoạn kết."
    response = await build_service(
        provider,
        page_service=FakePageContextService(page_text),
    ).chat(
        ChatRequestV2(
            message="Giải thích đoạn này",
            document_id="doc-1",
            context=ChatContextV2(
                text_selection=TextSelection(
                    page_number=2,
                    selected_text="Cơ chế attention cho phép mô hình tập trung",
                )
            ),
        )
    )

    assert response.trace.intent == "TEXT_SELECTION_CHAT"
    assert response.trace.image_used is False
    assert "Cơ chế attention" in provider.calls[0]["messages"][-1]["content"]
    assert response.citations[0].page_number == 2


@pytest.mark.asyncio
async def test_forged_text_selection_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        await build_service(
            FakeProvider(),
            page_service=FakePageContextService("Nội dung thật của trang."),
        ).chat(
            ChatRequestV2(
                message="Giải thích đoạn này",
                document_id="doc-1",
                context=ChatContextV2(
                    text_selection=TextSelection(
                        page_number=1,
                        selected_text="Nội dung giả hoàn toàn không tồn tại",
                    )
                ),
            )
        )
    assert error.value.status_code == 400
    assert error.value.detail == "Đoạn được chọn không khớp với nội dung trang PDF."


@pytest.mark.asyncio
async def test_visual_region_sends_crop_and_returns_citation(tmp_path: Path) -> None:
    provider = FakeProvider()
    visual = FakeVisualContextService(tmp_path)
    bbox = BBox(x=0.1, y=0.2, width=0.4, height=0.3)
    response = await build_service(provider, visual_service=visual).chat(
        ChatRequestV2(
            message="Giải thích biểu đồ này",
            document_id="doc-1",
            context=ChatContextV2(
                visual_region=VisualRegion(page_number=3, bbox=bbox)
            ),
        )
    )

    assert visual.crop_calls == [("doc-1", 3, bbox)]
    assert provider.calls[0]["image_bytes"]
    assert response.trace.intent == "VISUAL_REGION_CHAT"
    assert response.trace.image_used is True
    assert response.citations[0].page_number == 3


@pytest.mark.asyncio
async def test_document_text_search_uses_one_retrieval_and_real_citation() -> None:
    result = RetrievalResult(
        chunk={
            "chunk_id": "chunk-7",
            "page_number": 7,
            "text": "Bằng chứng về cơ chế residual connection.",
        },
        score=0.91,
        debug={},
    )
    retrieval = FakeRetrievalService([result])
    provider = FakeProvider()
    response = await build_service(provider, retrieval_service=retrieval).chat(
        ChatRequestV2(
            message="Residual connection có tác dụng gì?",
            document_id="doc-1",
            context=ChatContextV2(),
        )
    )

    assert retrieval.calls == [("doc-1", "Residual connection có tác dụng gì?", 4)]
    assert "Bằng chứng về cơ chế residual" in provider.calls[0]["messages"][-1]["content"]
    assert response.citations[0].page_number == 7


@pytest.mark.asyncio
async def test_document_term_query_uses_retrieval_variants_and_real_evidence() -> None:
    chunks = [
        {
            "chunk_id": "chunk-encoder",
            "document_id": "doc-1",
            "document_version": 1,
            "page_number": 3,
            "heading": "Encoder",
            "text": "An encoder converts input tokens into contextual representations.",
        },
        {
            "chunk_id": "chunk-rag",
            "document_id": "doc-1",
            "document_version": 1,
            "page_number": 1,
            "heading": "RAG",
            "text": "RAG retrieves document evidence before generating answers with citations.",
        },
    ]
    provider = FakeProvider()
    response = await build_service(
        provider,
        document_service=FakeDocumentService(page_count=8),
        retrieval_service=build_term_retrieval(chunks),
    ).chat(
        ChatRequestV2(
            message="ENCODER LÀ GÌ",
            document_id="doc-1",
            context=ChatContextV2(active_page=1),
        )
    )

    prompt = provider.calls[0]["messages"][-1]["content"]
    assert response.trace.intent == "DOCUMENT_SEARCH_CHAT"
    assert response.citations[0].page_number == 3
    assert "An encoder converts input tokens" in prompt
    assert "RAG retrieves document evidence" not in prompt


@pytest.mark.asyncio
async def test_document_term_typo_is_corrected_from_document_vocabulary() -> None:
    chunks = [
        {
            "chunk_id": "chunk-overfitting",
            "document_id": "doc-1",
            "document_version": 1,
            "page_number": 4,
            "heading": "Overfitting",
            "text": "Overfitting happens when a model fits training data too closely.",
        }
    ]
    provider = FakeProvider()
    response = await build_service(
        provider,
        document_service=FakeDocumentService(page_count=8),
        retrieval_service=build_term_retrieval(chunks),
    ).chat(
        ChatRequestV2(
            message="overfiting nghĩa là gì",
            document_id="doc-1",
            context=ChatContextV2(),
        )
    )

    assert response.citations[0].page_number == 4
    assert "Overfitting happens" in provider.calls[0]["messages"][-1]["content"]


@pytest.mark.asyncio
async def test_document_term_no_evidence_does_not_create_fake_citation() -> None:
    chunks = [
        {
            "chunk_id": "chunk-rag",
            "document_id": "doc-1",
            "document_version": 1,
            "page_number": 1,
            "heading": "RAG",
            "text": "RAG retrieves document evidence before generating answers with citations.",
        }
    ]
    provider = FakeProvider()
    response = await build_service(
        provider,
        retrieval_service=build_term_retrieval(chunks),
    ).chat(
        ChatRequestV2(
            message="xyzabc là gì",
            document_id="doc-1",
            context=ChatContextV2(),
        )
    )

    assert response.citations == []
    assert response.confidence == 0.25
    assert "Không tìm thấy bằng chứng phù hợp trong tài liệu." in provider.calls[0]["messages"][-1]["content"]


@pytest.mark.asyncio
async def test_ambiguous_prefix_typo_is_not_silently_rewritten() -> None:
    chunks = [
        {
            "chunk_id": "chunk-encoder",
            "document_id": "doc-1",
            "document_version": 1,
            "page_number": 3,
            "heading": "Encoder",
            "text": "Encoder maps input tokens.",
        },
        {
            "chunk_id": "chunk-encoding",
            "document_id": "doc-1",
            "document_version": 1,
            "page_number": 4,
            "heading": "Encoding",
            "text": "Encoding creates token representations.",
        },
    ]
    provider = FakeProvider()
    response = await build_service(
        provider,
        document_service=FakeDocumentService(page_count=8),
        retrieval_service=build_term_retrieval(chunks),
    ).chat(
        ChatRequestV2(
            message="encod là gì",
            document_id="doc-1",
            context=ChatContextV2(),
        )
    )

    assert response.citations == []
    assert "Không tìm thấy bằng chứng phù hợp trong tài liệu." in provider.calls[0]["messages"][-1]["content"]


@pytest.mark.asyncio
async def test_exact_figure_lookup_keeps_caption_page(tmp_path: Path) -> None:
    document_service = FakeDocumentService(page_count=8)
    document_service.repository = SimpleNamespace(
        list_pages=lambda document_id: [
            {"page_number": 3, "raw_text": "Figure 1: Encoder-decoder architecture"}
        ]
    )
    retrieval = FakeRetrievalService(
        [
            RetrievalResult(
                chunk={"chunk_id": "wrong", "page_number": 5, "text": "Nội dung khác"},
                score=0.99,
                debug={},
            )
        ]
    )
    visual = FakeVisualContextService(tmp_path)
    response = await build_service(
        FakeProvider(),
        document_service=document_service,
        visual_service=visual,
        retrieval_service=retrieval,
    ).chat(
        ChatRequestV2(
            message="Figure 1 biểu diễn gì?",
            document_id="doc-1",
            context=ChatContextV2(),
        )
    )

    assert visual.page_calls == [("doc-1", 3)]
    assert response.trace.pages_used[0] == 3
    assert response.citations[0].page_number == 3
