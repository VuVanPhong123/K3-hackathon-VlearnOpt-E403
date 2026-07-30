from __future__ import annotations

import fitz
from fastapi import HTTPException

from app.schemas import DocumentMetadata, PageContextResponse
from app.services.document_service import DocumentService


class PageContextService:
    def __init__(self, document_service: DocumentService | None = None) -> None:
        self.document_service = document_service or DocumentService()

    def get_page_text(self, document_id: str, page_number: int) -> PageContextResponse:
        metadata: DocumentMetadata = self.document_service.get_metadata(document_id)
        if page_number < 1 or page_number > metadata.page_count:
            raise HTTPException(status_code=400, detail="Trang PDF không hợp lệ.")

        path = self.document_service.get_file_path(document_id)
        try:
            with fitz.open(path) as pdf:
                page = pdf.load_page(page_number - 1)
                text = page.get_text("text").strip()
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Không thể đọc nội dung trang PDF.") from exc

        return PageContextResponse(
            document_id=document_id,
            page_number=page_number,
            text=text,
            has_text=bool(text),
        )
