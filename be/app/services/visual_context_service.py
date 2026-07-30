from __future__ import annotations

import hashlib
from pathlib import Path

import fitz
from fastapi import HTTPException

from app.config import settings
from app.schemas import BBox
from app.services.document_service import DocumentService


class VisualContextService:
    def __init__(self, document_service: DocumentService | None = None) -> None:
        self.document_service = document_service or DocumentService()
        self.cache_dir = settings.page_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def render_crop(self, document_id: str, page_number: int, bbox: BBox) -> Path:
        path = self.document_service.get_file_path(document_id)
        cache_key = hashlib.sha256(
            f"{document_id}:{page_number}:{bbox.x}:{bbox.y}:{bbox.width}:{bbox.height}".encode("utf-8")
        ).hexdigest()[:24]
        output = self.cache_dir / f"{cache_key}.png"
        if output.exists():
            return output
        try:
            with fitz.open(path) as pdf:
                page = pdf.load_page(page_number - 1)
                rect = page.rect
                clip = fitz.Rect(
                    bbox.x * rect.width,
                    bbox.y * rect.height,
                    min(1.0, bbox.x + bbox.width) * rect.width,
                    min(1.0, bbox.y + bbox.height) * rect.height,
                )
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip, alpha=False)
                pix.save(output)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Could not render visual region.") from exc
        return output
