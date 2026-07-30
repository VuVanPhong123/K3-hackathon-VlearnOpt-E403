from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import fitz
from fastapi import HTTPException

from app.schemas import BBox, DocumentMetadata, PageContextResponse
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.page_extraction_service import PageExtractionService
from app.services.section_service import SectionService


DEFAULT_DOCUMENT_ID = "d2-slide-hackathon"


class PdfEvalDocumentRepository:
    def __init__(self, pages: list[dict[str, Any]]) -> None:
        self.pages = pages

    def get_page(self, document_id: str, page_number: int) -> dict[str, Any] | None:
        for page in self.list_pages(document_id):
            if int(page["page_number"]) == page_number:
                return page
        return None

    def list_pages(self, document_id: str) -> list[dict[str, Any]]:
        return [page for page in self.pages if page["document_id"] == document_id]


class PdfEvalChunkRepository:
    def __init__(self, chunks: list[dict[str, Any]]) -> None:
        self.chunks = chunks

    def list_chunks(self, document_id: str) -> list[dict[str, Any]]:
        return [chunk for chunk in self.chunks if chunk["document_id"] == document_id]


class PdfEvalDocumentService:
    def __init__(self, metadata: DocumentMetadata, pdf_path: Path, repository: PdfEvalDocumentRepository) -> None:
        self.metadata = metadata
        self.pdf_path = pdf_path
        self.repository = repository

    def get_metadata(self, document_id: str) -> DocumentMetadata:
        if document_id != self.metadata.id:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
        return self.metadata

    def get_file_path(self, document_id: str) -> Path:
        self.get_metadata(document_id)
        return self.pdf_path


class PdfEvalPageContextService:
    def __init__(self, document_service: PdfEvalDocumentService) -> None:
        self.document_service = document_service

    def get_page_text(self, document_id: str, page_number: int) -> PageContextResponse:
        metadata = self.document_service.get_metadata(document_id)
        if page_number < 1 or page_number > metadata.page_count:
            raise HTTPException(
                status_code=400,
                detail=f"Tài liệu chỉ có {metadata.page_count} trang; không có trang {page_number}.",
            )
        page = self.document_service.repository.get_page(document_id, page_number)
        if not page:
            raise HTTPException(status_code=400, detail="Trang PDF không hợp lệ.")
        return PageContextResponse(
            document_id=document_id,
            page_number=page_number,
            text=page.get("raw_text", ""),
            has_text=bool(page.get("has_text")),
            blocks=page.get("blocks", []),
            requires_vision=bool(page.get("requires_vision")),
        )


class PdfEvalVisualContextService:
    def __init__(self, document_service: PdfEvalDocumentService, cache_dir: Path) -> None:
        self.document_service = document_service
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.diagnostics: list[dict[str, Any]] = []

    def render_page(self, document_id: str, page_number: int, scale: float | None = None) -> Path:
        metadata = self.document_service.get_metadata(document_id)
        self._validate_page(metadata.page_count, page_number)
        scale = scale or 1.6
        output = self.cache_dir / f"{document_id}-p{page_number:04d}-full.png"
        return self._render(page_number, scale, output, kind="page")

    def render_crop(self, document_id: str, page_number: int, bbox: BBox, scale: float | None = None) -> Path:
        metadata = self.document_service.get_metadata(document_id)
        self._validate_page(metadata.page_count, page_number)
        padded = self._padded_bbox(bbox)
        scale = scale or 2.0
        key = f"{padded.x:.4f}-{padded.y:.4f}-{padded.width:.4f}-{padded.height:.4f}".replace(".", "_")
        output = self.cache_dir / f"{document_id}-p{page_number:04d}-crop-{key}.png"
        return self._render(page_number, scale, output, bbox=padded, kind="crop")

    def get_overlapping_text(self, document_id: str, page_number: int, bbox: BBox) -> str:
        metadata = self.document_service.get_metadata(document_id)
        self._validate_page(metadata.page_count, page_number)
        page = self.document_service.repository.get_page(document_id, page_number)
        blocks = page.get("blocks", []) if page else []
        region = (bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height)
        texts: list[str] = []
        for block in blocks:
            block_bbox = block.get("bbox_norm") or []
            if len(block_bbox) != 4:
                continue
            x, y, width, height = block_bbox
            if self._intersects(region, (x, y, x + width, y + height)):
                text = (block.get("text") or "").strip()
                if text:
                    texts.append(text)
        return "\n".join(texts)

    def _render(
        self,
        page_number: int,
        scale: float,
        output: Path,
        *,
        bbox: BBox | None = None,
        kind: str,
    ) -> Path:
        if output.exists():
            return output
        with fitz.open(self.document_service.pdf_path) as pdf:
            page = pdf.load_page(page_number - 1)
            rect = page.rect
            clip = None
            if bbox:
                clip = fitz.Rect(
                    bbox.x * rect.width,
                    bbox.y * rect.height,
                    (bbox.x + bbox.width) * rect.width,
                    (bbox.y + bbox.height) * rect.height,
                )
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
            data = pix.tobytes("png")
            output.write_bytes(data)
        self.diagnostics.append(
            {
                "kind": kind,
                "page_number": page_number,
                "path_name": output.name,
                "byte_length": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "width": pix.width,
                "height": pix.height,
            }
        )
        return output

    @staticmethod
    def _validate_page(page_count: int, page_number: int) -> None:
        if page_number < 1 or page_number > page_count:
            raise HTTPException(status_code=400, detail="Trang PDF không hợp lệ.")

    @staticmethod
    def _padded_bbox(bbox: BBox) -> BBox:
        if bbox.width < 0.02 or bbox.height < 0.02:
            raise HTTPException(status_code=400, detail="Vùng được chọn quá nhỏ. Hãy khoanh lại rõ hơn.")
        padding = 0.03
        x = max(0.0, bbox.x - padding)
        y = max(0.0, bbox.y - padding)
        right = min(1.0, bbox.x + bbox.width + padding)
        bottom = min(1.0, bbox.y + bbox.height + padding)
        return BBox(x=x, y=y, width=max(0.001, right - x), height=max(0.001, bottom - y))

    @staticmethod
    def _intersects(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
        left = max(a[0], b[0])
        top = max(a[1], b[1])
        right = min(a[2], b[2])
        bottom = min(a[3], b[3])
        return right > left and bottom > top


@dataclass
class PdfEvalFixture:
    document_id: str
    pdf_path: Path
    metadata: DocumentMetadata
    pages: list[dict[str, Any]]
    sections: list[dict[str, Any]]
    chunks: list[dict[str, Any]]
    document_repository: PdfEvalDocumentRepository
    chunk_repository: PdfEvalChunkRepository
    document_service: PdfEvalDocumentService
    page_context_service: PdfEvalPageContextService
    visual_context_service: PdfEvalVisualContextService
    embedding_provider: HashEmbeddingProvider
    manifest: dict[str, Any]

    @classmethod
    def from_pdf(
        cls,
        pdf_path: Path,
        temp_dir: Path,
        *,
        document_id: str = DEFAULT_DOCUMENT_ID,
    ) -> "PdfEvalFixture":
        path = pdf_path.expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy PDF eval: {path}")
        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Eval document phải là PDF: {path.name}")

        data = path.read_bytes()
        checksum = hashlib.sha256(data).hexdigest()
        size_bytes = len(data)
        with fitz.open(path) as pdf:
            page_count = pdf.page_count
        original_filename = _original_filename(path)

        pages = PageExtractionService().extract(path, document_id, 1)
        sections = SectionService().detect_sections(document_id, 1, pages)
        chunks = ChunkingService().create_chunks(document_id, 1, pages, sections)
        embedding_provider = HashEmbeddingProvider()
        embeddings = EmbeddingService(embedding_provider).embed_chunks(chunks)
        for chunk in chunks:
            chunk["embedding"] = embeddings[chunk["chunk_id"]]

        metadata = DocumentMetadata(
            id=document_id,
            original_filename=original_filename,
            stored_filename=path.name,
            checksum_sha256=checksum,
            version=1,
            page_count=page_count,
            size_bytes=size_bytes,
            uploaded_at=datetime.now(UTC).isoformat(),
            status="READY",
            text_page_count=sum(1 for page in pages if page.get("has_text")),
            visual_only_page_count=sum(1 for page in pages if page.get("requires_vision")),
            chunk_count=len(chunks),
            indexed_at=datetime.now(UTC).isoformat(),
        )
        document_repository = PdfEvalDocumentRepository(pages)
        chunk_repository = PdfEvalChunkRepository(chunks)
        document_service = PdfEvalDocumentService(metadata, path, document_repository)
        page_context_service = PdfEvalPageContextService(document_service)
        visual_context_service = PdfEvalVisualContextService(document_service, temp_dir / "page-cache")
        manifest = {
            "filename": original_filename,
            "sha256": checksum,
            "size_bytes": size_bytes,
            "page_count": page_count,
        }
        return cls(
            document_id=document_id,
            pdf_path=path,
            metadata=metadata,
            pages=pages,
            sections=sections,
            chunks=chunks,
            document_repository=document_repository,
            chunk_repository=chunk_repository,
            document_service=document_service,
            page_context_service=page_context_service,
            visual_context_service=visual_context_service,
            embedding_provider=embedding_provider,
            manifest=manifest,
        )


def _original_filename(path: Path) -> str:
    metadata_path = path.parents[1] / "metadata" / f"{path.stem}.json" if len(path.parents) > 1 else None
    if metadata_path and metadata_path.exists():
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            original = Path(str(data.get("original_filename") or "")).name
            if original.lower().endswith(".pdf"):
                return original
        except (OSError, json.JSONDecodeError):
            pass
    return path.name
