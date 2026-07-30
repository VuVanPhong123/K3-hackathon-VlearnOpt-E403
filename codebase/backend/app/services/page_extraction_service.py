from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz


class PageExtractionService:
    min_text_chars = 25

    def extract(self, path: Path, document_id: str, version: int) -> list[dict[str, Any]]:
        pages: list[dict[str, Any]] = []
        with fitz.open(path) as pdf:
            for index, page in enumerate(pdf, start=1):
                rect = page.rect
                raw_text = page.get_text("text").strip()
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
                            "bbox": [float(x0), float(y0), float(x1), float(y1)],
                            "bbox_norm": [
                                float(x0 / rect.width) if rect.width else 0.0,
                                float(y0 / rect.height) if rect.height else 0.0,
                                float((x1 - x0) / rect.width) if rect.width else 0.0,
                                float((y1 - y0) / rect.height) if rect.height else 0.0,
                            ],
                        }
                    )
                text_length = len(raw_text)
                has_text = text_length >= self.min_text_chars
                pages.append(
                    {
                        "document_id": document_id,
                        "document_version": version,
                        "page_number": index,
                        "raw_text": raw_text,
                        "blocks": blocks,
                        "width": float(rect.width),
                        "height": float(rect.height),
                        "has_text": has_text,
                        "text_length": text_length,
                        "requires_vision": not has_text,
                    }
                )
        return pages
