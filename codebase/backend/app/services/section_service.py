from __future__ import annotations

import re
from typing import Any

from app.services.text_utils import search_normalize


HEADING_KEYWORDS = ("muc tieu", "noi dung", "phan", "chuong", "section", "chapter", "lesson")


class SectionService:
    def detect_sections(self, document_id: str, version: int, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for page in pages:
            title = self._detect_page_heading(page)
            if title:
                candidates.append(
                    {
                        "section_id": f"{document_id}-v{version}-s{len(candidates) + 1:04d}",
                        "document_id": document_id,
                        "document_version": version,
                        "title": title,
                        "start_page": page["page_number"],
                        "end_page": page["page_number"],
                    }
                )
        if not candidates:
            return [
                {
                    "section_id": f"{document_id}-v{version}-p{page['page_number']:04d}",
                    "document_id": document_id,
                    "document_version": version,
                    "title": f"Trang {page['page_number']}",
                    "start_page": page["page_number"],
                    "end_page": page["page_number"],
                }
                for page in pages
            ]
        for index, section in enumerate(candidates):
            if index + 1 < len(candidates):
                section["end_page"] = max(section["start_page"], candidates[index + 1]["start_page"] - 1)
            else:
                section["end_page"] = pages[-1]["page_number"] if pages else section["start_page"]
        return candidates

    def section_for_page(self, sections: list[dict[str, Any]], page_number: int) -> dict[str, Any] | None:
        for section in sections:
            if section["start_page"] <= page_number <= section["end_page"]:
                return section
        return None

    @staticmethod
    def _detect_page_heading(page: dict[str, Any]) -> str | None:
        for block in page.get("blocks", [])[:3]:
            first_line = block.get("text", "").strip().splitlines()[0:1]
            if not first_line:
                continue
            line = first_line[0].strip()
            normalized = search_normalize(line)
            if len(line) <= 90 and (
                re.match(r"^(\d+[\.\)]|[ivx]+\.|chapter|section)\s+", normalized)
                or any(keyword in normalized for keyword in HEADING_KEYWORDS)
                or (line.isupper() and len(line) > 4)
            ):
                return line
        return None
