from fastapi import APIRouter

from app.schemas import ChatRequestV2, ChatResponseV2
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/api/v2", tags=["chat-v2"])
orchestration_service = OrchestrationService()


@router.post("/chat", response_model=ChatResponseV2)
async def chat_v2(request: ChatRequestV2) -> ChatResponseV2:
    return await orchestration_service.chat(request)
