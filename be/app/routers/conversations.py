from fastapi import APIRouter, HTTPException

from app.repositories.conversation_repository import ConversationRepository
from app.schemas import ConversationResponse, DeleteDocumentResponse

router = APIRouter(prefix="/api/conversations", tags=["conversations"])
repository = ConversationRepository()


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str) -> ConversationResponse:
    conversation = repository.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện.")
    return ConversationResponse(
        conversation_id=conversation_id,
        messages=repository.list_messages(conversation_id),
    )


@router.delete("/{conversation_id}", response_model=DeleteDocumentResponse)
async def delete_conversation(conversation_id: str) -> DeleteDocumentResponse:
    deleted = repository.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc trò chuyện.")
    return DeleteDocumentResponse(deleted=True, document_id=conversation_id)
