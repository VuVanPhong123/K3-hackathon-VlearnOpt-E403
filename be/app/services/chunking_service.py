from __future__ import annotations

from typing import Any

from app.services.section_service import SectionService
from app.services.text_utils import estimate_tokens, normalize_text


class ChunkingService:
    min_tokens = 90
    target_tokens = 360
    max_tokens = 620
    overlap_tokens = 70

    def __init__(self) -> None:
        self.section_service = SectionService()

    def create_chunks(
        self,
        document_id: str,
        version: int,
        pages: list[dict[str, Any]],
        sections: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        for page in pages:
            section = self.section_service.section_for_page(sections, page["page_number"])
            current_blocks: list[dict[str, Any]] = []
            current_text: list[str] = []
            current_tokens = 0
            for block in page.get("blocks", []):
                text = block.get("text", "").strip()
                if not text:
                    continue
                block_tokens = estimate_tokens(text)
                if current_blocks and current_tokens + block_tokens > self.max_tokens:
                    chunks.append(
                        self._build_chunk(document_id, version, page, section, len(chunks), current_blocks, current_text)
                    )
                    current_blocks, current_text, current_tokens = self._overlap(current_blocks, current_text)
                current_blocks.append(block)
                current_text.append(text)
                current_tokens += block_tokens
            if current_blocks:
                chunks.append(
                    self._build_chunk(document_id, version, page, section, len(chunks), current_blocks, current_text)
                )
        for index, chunk in enumerate(chunks):
            chunk["previous_chunk_id"] = chunks[index - 1]["chunk_id"] if index else None
            chunk["next_chunk_id"] = chunks[index + 1]["chunk_id"] if index + 1 < len(chunks) else None
        return chunks

    def _overlap(self, blocks: list[dict[str, Any]], texts: list[str]) -> tuple[list[dict[str, Any]], list[str], int]:
        keep_blocks: list[dict[str, Any]] = []
        keep_texts: list[str] = []
        total = 0
        for block, text in reversed(list(zip(blocks, texts))):
            total += estimate_tokens(text)
            keep_blocks.insert(0, block)
            keep_texts.insert(0, text)
            if total >= self.overlap_tokens:
                break
        return keep_blocks, keep_texts, total

    @staticmethod
    def _build_chunk(
        document_id: str,
        version: int,
        page: dict[str, Any],
        section: dict[str, Any] | None,
        index: int,
        blocks: list[dict[str, Any]],
        texts: list[str],
    ) -> dict[str, Any]:
        x0 = min((block["bbox"][0] for block in blocks), default=0.0)
        y0 = min((block["bbox"][1] for block in blocks), default=0.0)
        x1 = max((block["bbox"][2] for block in blocks), default=0.0)
        y1 = max((block["bbox"][3] for block in blocks), default=0.0)
        text = "\n".join(texts).strip()
        heading = section["title"] if section else f"Page {page['page_number']}"
        chunk_index = index + 1
        return {
            "chunk_id": f"{document_id}-v{version}-p{page['page_number']:04d}-c{chunk_index:04d}",
            "document_id": document_id,
            "document_version": version,
            "page_number": page["page_number"],
            "section_id": section["section_id"] if section else None,
            "heading": heading,
            "text": text,
            "normalized_text": normalize_text(text),
            "content_type": "text",
            "block_indexes": [block["index"] for block in blocks],
            "bbox": [x0, y0, x1, y1],
            "previous_chunk_id": None,
            "next_chunk_id": None,
            "token_estimate": estimate_tokens(text),
        }
