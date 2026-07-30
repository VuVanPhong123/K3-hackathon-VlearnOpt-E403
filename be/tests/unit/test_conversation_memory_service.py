from __future__ import annotations

from app.config import settings
from app.schemas import ChatHistoryItem
from app.services.conversation_memory_service import ConversationMemoryService


class MemoryRepository:
    def __init__(self, messages=None, summary: str = "") -> None:
        self.messages = messages or []
        self.summary = summary

    def get_conversation(self, conversation_id: str):
        return {"summary": self.summary}

    def list_messages(self, conversation_id: str, limit: int = 100):
        return self.messages[-limit:]

    def count_messages(self, conversation_id: str) -> int:
        return len(self.messages)

    def update_summary(self, conversation_id: str, summary: str) -> None:
        self.summary = summary


def test_memory_uses_recent_window_and_compacts_old_messages(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chat_recent_message_limit", 12)
    monkeypatch.setattr(settings, "chat_summary_trigger_messages", 16)
    monkeypatch.setattr(settings, "chat_summary_max_chars", 4000)
    monkeypatch.setattr(settings, "chat_max_history_chars", 24000)
    messages = [
        {"role": "user" if index % 2 == 0 else "assistant", "content": f"message-{index}"}
        for index in range(20)
    ]
    repository = MemoryRepository(messages)

    context = ConversationMemoryService(repository).context_for(
        conversation_id="conversation-1",
        fallback_history=[],
    )

    assert context[0].role == "assistant"
    assert "Tóm tắt hội thoại trước" in context[0].content
    assert "message-0" in context[0].content
    assert [item.content for item in context[-12:]] == [f"message-{index}" for index in range(8, 20)]
    assert "message-0" in repository.summary


def test_memory_applies_character_budget(monkeypatch) -> None:
    monkeypatch.setattr(settings, "chat_recent_message_limit", 12)
    monkeypatch.setattr(settings, "chat_summary_trigger_messages", 99)
    monkeypatch.setattr(settings, "chat_max_history_chars", 20)
    fallback = [
        ChatHistoryItem(role="user", content="old message that should be trimmed"),
        ChatHistoryItem(role="assistant", content="latest important"),
    ]

    context = ConversationMemoryService(MemoryRepository([])).context_for(
        conversation_id=None,
        fallback_history=fallback,
    )

    assert len("".join(item.content for item in context)) <= 20
    assert context[-1].content.endswith("latest important")
