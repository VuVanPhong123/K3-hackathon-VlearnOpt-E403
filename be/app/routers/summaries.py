from fastapi import APIRouter, Query

from app.schemas import Citation, SummaryResponse
from app.services.document_service import DocumentService
from app.services.summary_service import SummaryService

router = APIRouter(prefix="/api/documents", tags=["summaries"])
document_service = DocumentService()
summary_service = SummaryService()


@router.get("/{document_id}/summary", response_model=SummaryResponse)
async def get_summary(document_id: str, type: str = Query(default="short")) -> SummaryResponse:
    document_service.get_metadata(document_id)
    result = summary_service.summarize(document_id, type)
    return SummaryResponse(
        document_id=document_id,
        summary_type=type,
        answer=result["answer"],
        citations=[Citation(**citation) for citation in result["citations"]],
    )
