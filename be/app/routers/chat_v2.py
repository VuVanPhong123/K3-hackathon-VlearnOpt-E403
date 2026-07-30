import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas import ChatRequestV2, ChatResponseV2
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/api/v2", tags=["chat-v2"])
orchestration_service = OrchestrationService()


@router.post("/chat", response_model=ChatResponseV2)
async def chat_v2(request: ChatRequestV2) -> ChatResponseV2:
    return await orchestration_service.chat(request)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat/stream")
async def chat_v2_stream(request: ChatRequestV2) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        async for item in orchestration_service.stream(request):
            yield _sse(item["event"], item["data"])

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
