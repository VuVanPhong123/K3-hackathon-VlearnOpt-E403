from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str


class DocumentMetadata(BaseModel):
    id: str
    original_filename: str
    stored_filename: str
    checksum_sha256: str = ""
    version: int = 1
    page_count: int = 0
    size_bytes: int
    uploaded_at: str
    status: Literal["UPLOADED", "PROCESSING", "READY", "FAILED", "DELETING", "NEEDS_INDEX"] = "UPLOADED"
    processing_error: str | None = None
    text_page_count: int = 0
    visual_only_page_count: int = 0
    chunk_count: int = 0
    indexed_at: str | None = None


class DeleteDocumentResponse(BaseModel):
    deleted: bool
    document_id: str


class PageContextResponse(BaseModel):
    document_id: str
    page_number: int
    text: str
    has_text: bool
    blocks: list[dict[str, Any]] = Field(default_factory=list)
    requires_vision: bool = False


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


class BBox(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)


class TextSelection(BaseModel):
    page_number: int = Field(ge=1)
    selected_text: str = Field(default="", max_length=6000)
    bounding_boxes: list[BBox] = Field(default_factory=list)


class VisualRegion(BaseModel):
    page_number: int = Field(ge=1)
    bbox: BBox


class ChatContextV2(BaseModel):
    active_page: int | None = Field(default=None, ge=1)
    attached_pages: list[int] = Field(default_factory=list)
    page_range: list[int] | None = None
    text_selection: TextSelection | None = None
    visual_region: VisualRegion | None = None


class ChatRequestV2(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None
    history: list[ChatHistoryItem] = Field(default_factory=list)
    document_id: str | None = None
    context: ChatContextV2 = Field(default_factory=ChatContextV2)
    answer_mode: Literal["document_only", "allow_general_knowledge"] = "document_only"
    requested_output: str | None = None


class Citation(BaseModel):
    document_id: str | None = None
    page_number: int | None = None
    page_start: int | None = None
    page_end: int | None = None
    chunk_id: str | None = None
    section_id: str | None = None
    label: str | None = None


class TraceInfo(BaseModel):
    trace_id: str
    intent: str
    pages_used: list[int] = Field(default_factory=list)
    provider: str = "deterministic"
    model: str = ""
    fallback: bool = False
    latency_ms: dict[str, float] = Field(default_factory=dict)
    confidence: float = 0.0


class ChatResponseV2(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float
    needs_clarification: bool = False
    abstained: bool = False
    conversation_id: str
    trace: TraceInfo
    debug: dict[str, Any] | None = None


class DocumentStatusResponse(BaseModel):
    status: str
    stage: str | None = None
    progress: int = Field(default=0, ge=0, le=100)
    error: str | None = None


class SearchResultItem(BaseModel):
    chunk_id: str
    page_number: int
    heading: str | None = None
    snippet: str
    score: float


class SearchResponse(BaseModel):
    document_id: str
    query: str
    results: list[SearchResultItem]


class SummaryResponse(BaseModel):
    document_id: str
    summary_type: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    conversation_id: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
