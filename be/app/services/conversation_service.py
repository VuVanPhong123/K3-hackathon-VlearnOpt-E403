from __future__ import annotations

import uuid

from app.repositories.conversation_repository import ConversationRepository


class ConversationService:
    def __init__(self, repository: ConversationRepository | None = None) -> None:
        self.repository = repository or ConversationRepository()

    def conversation_id(self, value: str | None) -> str:
        if value:
            try:
                uuid.UUID(value)
                return value
            except ValueError:
                pass
        return str(uuid.uuid4())
