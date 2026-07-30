from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str


class DocumentMetadata(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    page_count: int
    size_bytes: int
    uploaded_at: str


class DeleteDocumentResponse(BaseModel):
    deleted: bool
    document_id: str


class PageContextResponse(BaseModel):
    document_id: str
    page_number: int
    text: str
    has_text: bool


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatHistoryItem] = Field(default_factory=list)
    document_id: str | None = None
    page_number: int | None = Field(default=None, ge=1)


class ChatResponse(BaseModel):
    answer: str
    provider: str
    model: str
    fallback_used: bool
    document_id: str | None = None
    page_number: int | None = None
