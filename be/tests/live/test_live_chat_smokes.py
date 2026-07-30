from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config import settings
from app.schemas import BBox, ChatContextV2, ChatRequestV2, VisualRegion
from app.services.orchestration_service import OrchestrationService
from app.services.page_context_service import PageContextService
from app.services.visual_context_service import VisualContextService
from tests.fixtures import create_fixture_pdf


class LiveDocumentRepository:
    def get_page(self, document_id: str, page_number: int):
        return None

    def list_pages(self, document_id: str):
        return []


class LiveDocumentService:
    def __init__(self, path) -> None:
        self.path = path
        self.repository = LiveDocumentRepository()
        self.metadata = SimpleNamespace(
            id="live-doc",
            original_filename="cp3-visual-fixture.pdf",
            page_count=9,
            version=1,
        )

    def get_metadata(self, document_id: str):
        assert document_id == "live-doc"
        return self.metadata

    def get_file_path(self, document_id: str):
        assert document_id == "live-doc"
        return self.path


class LiveConversationRepository:
    def ensure_conversation(self, *args, **kwargs) -> None:
        pass

    def add_message(self, *args, **kwargs) -> None:
        pass


@pytest.mark.asyncio
@pytest.mark.skipif(
    not (settings.openai_api_key or settings.gemini_api_key),
    reason="Chưa cấu hình API key cho live smoke.",
)
async def test_three_live_chat_smokes(tmp_path) -> None:
    pdf_path = create_fixture_pdf(tmp_path / "live-fixture.pdf")
    document_service = LiveDocumentService(pdf_path)
    service = OrchestrationService(
        document_service=document_service,
        page_context_service=PageContextService(document_service),
        visual_context_service=VisualContextService(document_service),
        conversation_repository=LiveConversationRepository(),
    )

    general = await service.chat(
        ChatRequestV2(
            message="Hãy trả lời ngắn gọn: một kế hoạch học tốt cần điều gì?",
            context=ChatContextV2(),
            answer_mode="allow_general_knowledge",
        )
    )
    assert general.answer.strip()
    assert general.provider and general.model
    assert general.citations == []

    full_page = await service.chat(
        ChatRequestV2(
            message="Giải thích Figure 1 dựa trên sơ đồ thật trong ảnh.",
            document_id="live-doc",
            context=ChatContextV2(attached_pages=[3]),
        )
    )
    assert full_page.answer.strip()
    assert full_page.provider and full_page.model
    assert full_page.trace.image_used is True
    assert full_page.citations[0].page_number == 3
    assert "không nhận được ảnh" not in full_page.answer.casefold()

    region = await service.chat(
        ChatRequestV2(
            message="Giải thích xu hướng của đường biểu diễn trong vùng này.",
            document_id="live-doc",
            context=ChatContextV2(
                visual_region=VisualRegion(
                    page_number=7,
                    bbox=BBox(x=0.12, y=0.17, width=0.76, height=0.58),
                )
            ),
        )
    )
    assert region.answer.strip()
    assert region.provider and region.model
    assert region.trace.image_used is True
    assert region.citations[0].page_number == 7
    assert "không nhận được ảnh" not in region.answer.casefold()
