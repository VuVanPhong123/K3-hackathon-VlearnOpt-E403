import pytest

from app.schemas import ChatContextV2, ChatRequestV2, TextSelection
from app.services.orchestration_service import OrchestrationService


@pytest.mark.asyncio
async def test_chat_v2_selection_answers() -> None:
    response = await OrchestrationService().chat(
        ChatRequestV2(
            message="giai thich",
            document_id="00000000-0000-0000-0000-000000000001",
            context=ChatContextV2(text_selection=TextSelection(page_number=2, selected_text="RAG citation evidence")),
        )
    )
    assert response.citations[0].page_number == 2
