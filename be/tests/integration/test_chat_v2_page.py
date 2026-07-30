import pytest

from app.schemas import ChatContextV2, ChatRequestV2
from app.services.orchestration_service import OrchestrationService


@pytest.mark.asyncio
async def test_chat_v2_without_document_abstains() -> None:
    response = await OrchestrationService().chat(ChatRequestV2(message="noi dung nay la gi", context=ChatContextV2()))
    assert response.abstained is True
