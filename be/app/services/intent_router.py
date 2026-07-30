from __future__ import annotations

import re

from app.domain.intents import Intent
from app.schemas import ChatRequestV2
from app.services.text_utils import search_normalize


class IntentRouter:
    def route(self, request: ChatRequestV2) -> tuple[Intent, float]:
        message = search_normalize(request.message)
        context = request.context
        if context.visual_region:
            return Intent.VISUAL_QA, 0.95
        if context.text_selection and context.text_selection.selected_text.strip():
            return Intent.SELECTION_QA, 0.95
        if any(token in message for token in ["tom tat", "tong hop", "outline", "key concept", "muc tieu hoc"]):
            return Intent.SUMMARY, 0.9
        if any(token in message for token in ["quiz", "cau hoi trac nghiem", "kiem tra hieu"]):
            return Intent.QUIZ, 0.86
        if "flashcard" in message or "the ghi nho" in message:
            return Intent.FLASHCARD, 0.86
        if any(token in message for token in ["so sanh", "khac nhau", "giong nhau"]):
            return Intent.COMPARE, 0.84
        if any(token in message for token in ["o dau", "trang nao", "vi tri", "nam dau"]):
            return Intent.FIND_LOCATION, 0.88
        if len(message.split()) <= 5 and any(token in message for token in ["no", "cai nay", "y thu hai"]):
            return Intent.CLARIFY, 0.55
        if any(token in message for token in ["thoi tiet", "bong da", "mua co phieu", "dat ve"]):
            return Intent.OUT_OF_SCOPE, 0.75
        if context.attached_pages or re.search(r"\btrang\s*\d+\b", message):
            return Intent.PAGE_QA, 0.88
        if request.document_id:
            return Intent.DOCUMENT_SEARCH, 0.78
        return Intent.GENERAL_CHAT, 0.7
