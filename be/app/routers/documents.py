from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from app.schemas import DeleteDocumentResponse, DocumentMetadata, PageContextResponse
from app.services.document_service import DocumentService
from app.services.page_context_service import PageContextService

router = APIRouter(prefix="/api/documents", tags=["documents"])
document_service = DocumentService()
page_context_service = PageContextService(document_service)


@router.post("", response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...)) -> DocumentMetadata:
    return await document_service.save_upload(file)


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
