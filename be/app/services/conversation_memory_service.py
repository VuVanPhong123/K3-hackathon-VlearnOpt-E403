from __future__ import annotations

import re

from app.config import settings
from app.repositories.conversation_repository import ConversationRepository
from app.schemas import ChatHistoryItem


class ConversationMemoryService:
    def __init__(self, repository: ConversationRepository | None = None) -> None:
        self.repository = repository or ConversationRepository()

    def context_for(
        self,
        *,
        conversation_id: str | None,
        fallback_history: list[ChatHistoryItem],
    ) -> list[ChatHistoryItem]:
        messages: list[dict] = []
        summary = ""
        if conversation_id and hasattr(self.repository, "get_conversation"):
            conversation = self.repository.get_conversation(conversation_id)
            if conversation:
                summary = str(conversation.get("summary") or "")
                messages = self.repository.list_messages(
                    conversation_id,
                    limit=max(
                        settings.chat_summary_trigger_messages,
                        settings.chat_recent_message_limit,
                    )
                    + 24,
                )
                if self.repository.count_messages(conversation_id) >= settings.chat_summary_trigger_messages:
                    summary = self.compact(conversation_id)

        if not messages:
            messages = [
                {"role": item.role, "content": item.content}
                for item in fallback_history
            ]

        recent = self._recent_items(messages, settings.chat_recent_message_limit)
        items: list[ChatHistoryItem] = []
        if summary.strip():
            items.append(
                ChatHistoryItem(
                    role="assistant",
                    content=f"Tóm tắt hội thoại trước:\n{self._clean(summary)}",
                )
            )
        items.extend(
            ChatHistoryItem(role=item["role"], content=self._clean(item["content"]))
            for item in recent
            if item.get("role") in {"user", "assistant"} and self._clean(item.get("content", ""))
        )
        return self._apply_budget(items)

    def compact(self, conversation_id: str) -> str:
        all_messages = self.repository.list_messages(conversation_id, limit=10_000)
        old_messages = all_messages[:-settings.chat_recent_message_limit]
        lines = []
        for item in old_messages:
            role = "Người dùng" if item.get("role") == "user" else "Trợ lý"
            content = self._clean(str(item.get("content") or ""))
            if not content:
                continue
            lines.append(f"{role}: {content[:800]}")
        digest = "\n".join(lines)
        if len(digest) > settings.chat_summary_max_chars:
            digest = digest[-settings.chat_summary_max_chars:]
        self.repository.update_summary(conversation_id, digest)
        return digest

    @staticmethod
    def _recent_items(messages: list[dict], limit: int) -> list[dict]:
        filtered = [
            item
            for item in messages
            if item.get("role") in {"user", "assistant"} and str(item.get("content") or "").strip()
        ]
        return filtered[-limit:]

    @staticmethod
    def _clean(value: str) -> str:
        value = re.sub(r"sk-[A-Za-z0-9_-]+", "[redacted]", value)
        value = re.sub(r"AIza[A-Za-z0-9_-]+", "[redacted]", value)
        return re.sub(r"\s+", " ", value).strip()

    @staticmethod
    def _apply_budget(items: list[ChatHistoryItem]) -> list[ChatHistoryItem]:
        budget = settings.chat_max_history_chars
        selected: list[ChatHistoryItem] = []
        remaining = budget
        for item in reversed(items):
            content = item.content
            if len(content) > remaining:
                if item is items[-1]:
                    content = content[-remaining:]
                else:
                    continue
            selected.append(ChatHistoryItem(role=item.role, content=content))
            remaining -= len(content)
            if remaining <= 0:
                break
        return list(reversed(selected))
