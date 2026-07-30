from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse
from app.services.llm_service import LLMService

router = APIRouter(prefix="/api", tags=["chat"])
llm_service = LLMService()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    return await llm_service.chat(request)
