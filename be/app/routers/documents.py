from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import DeleteDocumentResponse, DocumentMetadata, DocumentStatusResponse, PageContextResponse, SearchResponse, SearchResultItem
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService
from app.services.page_context_service import PageContextService
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/api/documents", tags=["documents"])
document_service = DocumentService()
page_context_service = PageContextService(document_service)
ingestion_service = IngestionService()
retrieval_service = RetrievalService()


@router.post("", response_model=DocumentMetadata)
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)) -> DocumentMetadata:
    metadata = await document_service.save_upload(file)
    if metadata.status in {"UPLOADED", "NEEDS_INDEX"}:
        background_tasks.add_task(ingestion_service.process_document, metadata.id, str(document_service.get_file_path(metadata.id)))
        metadata.status = "PROCESSING"
    return metadata


@router.get("", response_model=list[DocumentMetadata])
async def list_documents() -> list[DocumentMetadata]:
    return document_service.list_documents()


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str) -> DocumentMetadata:
    return document_service.get_metadata(document_id)


@router.get("/{document_id}/file")
async def get_document_file(document_id: str) -> FileResponse:
    metadata = document_service.get_metadata(document_id)
    path = document_service.get_file_path(document_id)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=metadata.original_filename,
        headers={"Content-Disposition": f'inline; filename="{metadata.original_filename}"'},
    )


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
async def delete_document(document_id: str) -> DeleteDocumentResponse:
    document_service.delete_document(document_id)
    return DeleteDocumentResponse(deleted=True, document_id=document_id)


@router.get("/{document_id}/pages/{page_number}/context", response_model=PageContextResponse)
async def get_page_context(document_id: str, page_number: int) -> PageContextResponse:
    return page_context_service.get_page_text(document_id, page_number)


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str) -> DocumentStatusResponse:
    metadata = document_service.get_metadata(document_id)
    job = document_service.repository.get_job(document_id)
    if job:
        return DocumentStatusResponse(**job)
    return DocumentStatusResponse(status=metadata.status, stage=None, progress=100 if metadata.status == "READY" else 0, error=metadata.processing_error)


@router.post("/{document_id}/reindex", response_model=DocumentStatusResponse)
async def reindex_document(document_id: str, background_tasks: BackgroundTasks) -> DocumentStatusResponse:
    if settings.app_env == "production" and not settings.enable_debug_endpoints:
        raise HTTPException(status_code=404, detail="Không tìm thấy.")
    metadata = document_service.get_metadata(document_id)
    background_tasks.add_task(ingestion_service.process_document, metadata.id, str(document_service.get_file_path(metadata.id)))
    return DocumentStatusResponse(status="PROCESSING", stage="queued", progress=0, error=None)


@router.get("/{document_id}/search", response_model=SearchResponse)
async def search_document(
    document_id: str,
    q: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(default=6, ge=1, le=20),
) -> SearchResponse:
    if settings.app_env == "production" and not settings.enable_debug_endpoints:
        raise HTTPException(status_code=404, detail="Không tìm thấy.")
    document_service.get_metadata(document_id)
    results = retrieval_service.debug_search(document_id, q, top_k)
    return SearchResponse(
        document_id=document_id,
        query=q,
        results=[
            SearchResultItem(
                chunk_id=item["chunk_id"],
                page_number=item["page_number"],
                heading=item["heading"],
                snippet=item["snippet"],
                score=item["score"],
            )
            for item in results
        ],
    )
