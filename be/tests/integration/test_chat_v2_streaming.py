from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.config import settings
from app.schemas import ChatContextV2, ChatRequestV2, PageContextResponse
from app.services.answer_service import AnswerService
from app.services.orchestration_service import OrchestrationService
from app.services.provider_gateway import ProviderGateway
from app.services.providers.base import ProviderResult, ProviderTemporaryError


class StreamingProvider:
    def __init__(
        self,
        name: str = "openai",
        chunks: list[str] | None = None,
        error_after_delta: Exception | None = None,
    ) -> None:
        self.name = name
        self.chunks = chunks or ["Xin ", "chào"]
        self.error_after_delta = error_after_delta

    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> ProviderResult:
        return ProviderResult(text="".join(self.chunks), provider=self.name, model=f"fake-{self.name}")

    async def generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResult:
        return ProviderResult(text="".join(self.chunks), provider=self.name, model=f"fake-{self.name}-vision")

    async def stream_generate(self, *, system_prompt: str, messages: list[dict[str, str]]):
        for chunk in self.chunks:
            yield chunk
            if self.error_after_delta:
                raise self.error_after_delta

    async def stream_generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ):
        for chunk in self.chunks:
            yield chunk
            if self.error_after_delta:
                raise self.error_after_delta


class RecordingConversationRepository:
    def __init__(self) -> None:
        self.conversations = {}
        self.messages = []

    def get_conversation(self, conversation_id: str):
        return self.conversations.get(conversation_id)

    def list_messages(self, conversation_id: str, limit: int = 100):
        return []

    def count_messages(self, conversation_id: str) -> int:
        return 0

    def ensure_conversation(self, conversation_id: str, document_id=None, document_version=None) -> None:
        self.conversations[conversation_id] = {"summary": "", "document_id": document_id}

    def add_message(self, conversation_id: str, role: str, content: str, citations=None, trace=None) -> None:
        self.messages.append(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "citations": citations or [],
                "trace": trace or {},
            }
        )


class FakeDocumentService:
    def __init__(self) -> None:
        self.repository = SimpleNamespace(list_pages=lambda document_id: [])

    def get_metadata(self, document_id: str):
        return SimpleNamespace(
            id=document_id,
            original_filename="bai-hoc.pdf",
            page_count=3,
            version=1,
            status="READY",
        )


class FakePageContextService:
    def get_page_text(self, document_id: str, page_number: int) -> PageContextResponse:
        return PageContextResponse(
            document_id=document_id,
            page_number=page_number,
            text="Nội dung trang đang được kiểm thử.",
            has_text=True,
        )


class FakeVisualContextService:
    def __init__(self, tmp_path: Path) -> None:
        self.path = tmp_path / "page.png"
        self.path.write_bytes(b"\x89PNG\r\n\x1a\nfixture")

    def render_page(self, document_id: str, page_number: int) -> Path:
        return self.path

    def render_crop(self, document_id: str, page_number: int, bbox) -> Path:
        return self.path

    def get_overlapping_text(self, document_id: str, page_number: int, bbox) -> str:
        return "Văn bản trong vùng."


def build_service(provider: StreamingProvider, repository, tmp_path: Path) -> OrchestrationService:
    gateway = ProviderGateway(lambda: provider, lambda: provider)
    return OrchestrationService(
        answer_service=AnswerService(gateway),
        document_service=FakeDocumentService(),
        page_context_service=FakePageContextService(),
        visual_context_service=FakeVisualContextService(tmp_path),
        conversation_repository=repository,
    )


@pytest.fixture(autouse=True)
def provider_settings(monkeypatch):
    monkeypatch.setattr(settings, "primary_text_provider", "openai")
    monkeypatch.setattr(settings, "fallback_text_provider", "gemini")
    monkeypatch.setattr(settings, "vision_primary_provider", "openai")
    monkeypatch.setattr(settings, "vision_fallback_provider", "gemini")
    monkeypatch.setattr(settings, "openai_api_key", "openai-test")
    monkeypatch.setattr(settings, "gemini_api_key", "gemini-test")


@pytest.mark.asyncio
async def test_stream_general_chat_emits_meta_delta_done_and_saves(tmp_path: Path) -> None:
    repository = RecordingConversationRepository()
    service = build_service(StreamingProvider(chunks=["Xin ", "chào."]), repository, tmp_path)

    events = [
        event
        async for event in service.stream(
            ChatRequestV2(message="Xin chào", context=ChatContextV2())
        )
    ]

    assert [event["event"] for event in events] == ["meta", "delta", "delta", "done"]
    assert events[0]["data"]["mode"] == "GENERAL_CHAT"
    assert events[-1]["data"]["answer"] == "Xin chào."
    assert [message["role"] for message in repository.messages] == ["user", "assistant"]
    assert repository.messages[-1]["content"] == "Xin chào."


@pytest.mark.asyncio
async def test_stream_page_chat_includes_citation_in_done(tmp_path: Path) -> None:
    repository = RecordingConversationRepository()
    service = build_service(StreamingProvider(chunks=["Trang ", "hai."]), repository, tmp_path)

    events = [
        event
        async for event in service.stream(
            ChatRequestV2(
                message="Giải thích trang này.",
                document_id="doc-1",
                context=ChatContextV2(attached_pages=[2]),
            )
        )
    ]

    assert events[0]["data"]["mode"] == "PAGE_CHAT"
    assert events[-1]["event"] == "done"
    assert events[-1]["data"]["citations"][0]["page_number"] == 2
    assert repository.messages[-1]["citations"][0]["page_number"] == 2


@pytest.mark.asyncio
async def test_stream_error_after_partial_delta_does_not_save_assistant(tmp_path: Path) -> None:
    repository = RecordingConversationRepository()
    service = build_service(
        StreamingProvider(
            chunks=["Một phần"],
            error_after_delta=ProviderTemporaryError("late timeout"),
        ),
        repository,
        tmp_path,
    )

    events = [
        event
        async for event in service.stream(
            ChatRequestV2(message="Xin chào", context=ChatContextV2())
        )
    ]

    assert [event["event"] for event in events] == ["meta", "delta", "error"]
    assert events[-1]["data"]["retryable"] is True
    assert repository.messages == []
