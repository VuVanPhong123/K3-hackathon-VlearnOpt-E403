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

    def render_page(self, document_id: str, page_number: int, scale: float | None = None) -> Path:
        metadata = self.document_service.get_metadata(document_id)
        self._validate_page(metadata.page_count, page_number)
        path = self.document_service.get_file_path(document_id)
        scale = scale or settings.page_render_scale
        cache_key = hashlib.sha256(
            f"page:{document_id}:{metadata.version}:{page_number}:{scale}".encode("utf-8")
        ).hexdigest()[:24]
        return self._render_cached(path, page_number, scale, self.cache_dir / f"{cache_key}.png")

    def render_crop(self, document_id: str, page_number: int, bbox: BBox, scale: float | None = None) -> Path:
        metadata = self.document_service.get_metadata(document_id)
        self._validate_page(metadata.page_count, page_number)
        padded = self._padded_bbox(bbox)
        scale = scale or settings.region_render_scale
        path = self.document_service.get_file_path(document_id)
        cache_key = hashlib.sha256(
            (
                f"crop:{document_id}:{metadata.version}:{page_number}:"
                f"{padded.x:.5f}:{padded.y:.5f}:{padded.width:.5f}:{padded.height:.5f}:{scale}"
            ).encode("utf-8")
        ).hexdigest()[:24]
        output = self.cache_dir / f"{cache_key}.png"
        if output.exists():
            return output
        try:
            with fitz.open(path) as pdf:
                page = pdf.load_page(page_number - 1)
                rect = page.rect
                clip = fitz.Rect(
                    padded.x * rect.width,
                    padded.y * rect.height,
                    (padded.x + padded.width) * rect.width,
                    (padded.y + padded.height) * rect.height,
                )
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
                output.write_bytes(pix.tobytes("png"))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Không thể hiển thị vùng hình ảnh.") from exc
        return output

    def get_overlapping_text(self, document_id: str, page_number: int, bbox: BBox) -> str:
        metadata = self.document_service.get_metadata(document_id)
        self._validate_page(metadata.page_count, page_number)
        page_context = self.document_service.repository.get_page(document_id, page_number)
        blocks = page_context["blocks"] if page_context else self._extract_blocks(document_id, page_number)
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

    def _render_cached(self, path: Path, page_number: int, scale: float, output: Path) -> Path:
        if output.exists():
            return output
        try:
            with fitz.open(path) as pdf:
                page = pdf.load_page(page_number - 1)
                rect = page.rect
                longest = max(rect.width, rect.height)
                effective_scale = min(scale, 2400 / longest) if longest else scale
                data = b""
                while effective_scale >= 0.8:
                    pix = page.get_pixmap(matrix=fitz.Matrix(effective_scale, effective_scale), alpha=False)
                    data = pix.tobytes("png")
                    if len(data) <= settings.max_visual_image_bytes:
                        output.write_bytes(data)
                        return output
                    effective_scale *= 0.85
                output.write_bytes(data)
                return output
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Không thể render trang PDF.") from exc

    def _extract_blocks(self, document_id: str, page_number: int) -> list[dict]:
        path = self.document_service.get_file_path(document_id)
        with fitz.open(path) as pdf:
            page = pdf.load_page(page_number - 1)
            rect = page.rect
            blocks = []
            for block_index, block in enumerate(page.get_text("blocks")):
                if len(block) < 5:
                    continue
                x0, y0, x1, y1, text = block[:5]
                text = (text or "").strip()
                if not text:
                    continue
                blocks.append(
                    {
                        "index": block_index,
                        "text": text,
                        "bbox_norm": [
                            float(x0 / rect.width) if rect.width else 0.0,
                            float(y0 / rect.height) if rect.height else 0.0,
                            float((x1 - x0) / rect.width) if rect.width else 0.0,
                            float((y1 - y0) / rect.height) if rect.height else 0.0,
                        ],
                    }
                )
            return blocks

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
