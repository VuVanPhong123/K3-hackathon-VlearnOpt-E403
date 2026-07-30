from __future__ import annotations

import re
from dataclasses import dataclass, field

from fastapi import HTTPException

from app.schemas import ChatRequestV2
from app.services.document_service import DocumentService


PAGE_PATTERNS = [
    re.compile(r"\b(?:trang|slide|page)\s*(?:s(?:o|ố)|thu|thứ)?\s*(\d{1,3})\b", re.IGNORECASE),
    re.compile(r"\bp\.\s*(\d{1,3})\b", re.IGNORECASE),
]
CURRENT_PAGE_RE = re.compile(r"\b(trang|slide|bang|bảng|hinh|hình)\s+n[aà]y\b", re.IGNORECASE)
SMALL_TALK_RE = re.compile(
    r"^\s*(xin\s+ch[aà]o|ch[aà]o|hello|hi|hey|c[aả]m\s+[oơ]n|thanks?|ok|okay)\s*[!.?]*\s*$",
    re.IGNORECASE,
)
VISUAL_QUERY_RE = re.compile(
    r"\b(h[iì]nh|figure|fig\.?|[aả]nh|b[aả]ng|table|bi[eể]u\s*[dđ][oồ]|chart|s[oơ]\s*[dđ][oồ]|diagram|architecture)\b",
    re.IGNORECASE,
)
CAPTION_RE = re.compile(r"\b(figure|fig\.?|h[iì]nh|table|b[aả]ng)\s*(\d{1,3})\b", re.IGNORECASE)


@dataclass
class ResolvedInteraction:
    mode: str
    page_number: int | None = None
    pages_used: list[int] = field(default_factory=list)
    confidence: float = 1.0
    visual_query: bool = False
    exact_caption: str | None = None


class InteractionResolver:
    def __init__(self, document_service: DocumentService | None = None) -> None:
        self.document_service = document_service or DocumentService()

    def resolve(self, request: ChatRequestV2) -> ResolvedInteraction:
        forced = request.interaction_mode
        context = request.context

        if forced == "general":
            return ResolvedInteraction(mode="GENERAL_CHAT", confidence=1.0)

        if context.visual_region and forced in {"auto", "visual_region"}:
            self._validate_page(request.document_id, context.visual_region.page_number)
            page = context.visual_region.page_number
            return ResolvedInteraction(mode="VISUAL_REGION_CHAT", page_number=page, pages_used=[page], visual_query=True)

        if context.text_selection and context.text_selection.selected_text.strip() and forced in {"auto", "text_selection"}:
            self._validate_page(request.document_id, context.text_selection.page_number)
            page = context.text_selection.page_number
            return ResolvedInteraction(mode="TEXT_SELECTION_CHAT", page_number=page, pages_used=[page])

        attached_pages = [page for page in context.attached_pages if page > 0]
        if attached_pages and forced in {"auto", "page"}:
            if len(attached_pages) > 1:
                raise HTTPException(status_code=400, detail="Chat hiện chỉ hỗ trợ gắn một trang PDF.")
            page = attached_pages[0]
            self._validate_page(request.document_id, page)
            return ResolvedInteraction(
                mode="PAGE_CHAT",
                page_number=page,
                pages_used=[page],
                visual_query=is_visual_query(request.message),
            )

        if forced == "page":
            page = extract_page_number(request.message)
            if page is None and context.active_page:
                page = context.active_page
            if page is None:
                raise HTTPException(status_code=400, detail="Cần chỉ định trang PDF để hỏi theo trang.")
            self._validate_page(request.document_id, page)
            return ResolvedInteraction(mode="PAGE_CHAT", page_number=page, pages_used=[page])

        explicit_page = extract_page_number(request.message)
        if explicit_page and request.document_id and forced == "auto":
            self._validate_page(request.document_id, explicit_page)
            return ResolvedInteraction(
                mode="PAGE_CHAT",
                page_number=explicit_page,
                pages_used=[explicit_page],
                visual_query=is_visual_query(request.message),
            )

        if CURRENT_PAGE_RE.search(request.message) and context.active_page and request.document_id and forced == "auto":
            self._validate_page(request.document_id, context.active_page)
            return ResolvedInteraction(
                mode="PAGE_CHAT",
                page_number=context.active_page,
                pages_used=[context.active_page],
                confidence=0.82,
                visual_query=is_visual_query(request.message),
            )

        if forced == "document_search":
            if not request.document_id:
                return ResolvedInteraction(mode="GENERAL_CHAT", confidence=0.6)
            return ResolvedInteraction(mode="DOCUMENT_SEARCH_CHAT", visual_query=is_visual_query(request.message))

        if request.answer_mode == "allow_general_knowledge" and forced == "auto":
            return ResolvedInteraction(mode="GENERAL_CHAT", confidence=1.0)

        if not request.document_id or is_small_talk(request.message):
            return ResolvedInteraction(mode="GENERAL_CHAT", confidence=1.0)

        return ResolvedInteraction(
            mode="DOCUMENT_SEARCH_CHAT",
            visual_query=is_visual_query(request.message),
            exact_caption=extract_caption_key(request.message),
            confidence=0.78,
        )

    def _validate_page(self, document_id: str | None, page_number: int) -> None:
        if not document_id:
            raise HTTPException(status_code=400, detail="Cần có tài liệu PDF để xử lý ngữ cảnh này.")
        metadata = self.document_service.get_metadata(document_id)
        if page_number < 1 or page_number > metadata.page_count:
            raise HTTPException(
                status_code=400,
                detail=f"Tài liệu chỉ có {metadata.page_count} trang; không có trang {page_number}.",
            )


def extract_page_number(message: str) -> int | None:
    normalized = message.lower()
    for pattern in PAGE_PATTERNS:
        for match in pattern.finditer(normalized):
            page = int(match.group(1))
            if 1 <= page <= 999:
                return page
    return None


def extract_caption_key(message: str) -> str | None:
    match = CAPTION_RE.search(message)
    if not match:
        return None
    label = match.group(1).lower().replace(".", "")
    number = match.group(2)
    if label in {"fig", "figure"}:
        return f"figure {number}"
    if label in {"hình", "hinh"}:
        return f"hình {number}"
    if label in {"bảng", "bang", "table"}:
        return f"table {number}"
    return None


def is_small_talk(message: str) -> bool:
    return bool(SMALL_TALK_RE.match(message))


def is_visual_query(message: str) -> bool:
    return bool(VISUAL_QUERY_RE.search(message))
