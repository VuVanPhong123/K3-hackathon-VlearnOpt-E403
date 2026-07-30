from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.repositories.database import Database, database


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ConversationRepository:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or database

    def ensure_conversation(
        self,
        conversation_id: str,
        document_id: str | None = None,
        document_version: int | None = None,
    ) -> None:
        now = now_iso()
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT INTO conversations(conversation_id, document_id, document_version, created_at, updated_at, summary)
                VALUES (?, ?, ?, ?, ?, NULL)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    document_id=excluded.document_id,
                    document_version=excluded.document_version,
                    updated_at=excluded.updated_at
                """,
                (conversation_id, document_id, document_version, now, now),
            )

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: list[dict[str, Any]] | None = None,
        trace: dict[str, Any] | None = None,
    ) -> None:
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_messages(conversation_id, role, content, citations_json, trace_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    conversation_id,
                    role,
                    content,
                    json.dumps(citations or [], ensure_ascii=False),
                    json.dumps(trace or {}, ensure_ascii=False),
                    now_iso(),
                ),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE conversation_id = ?",
                (now_iso(), conversation_id),
            )

    def list_messages(self, conversation_id: str, limit: int = 100) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            rows = connection.execute(
                """
                SELECT role, content, citations_json, trace_json, created_at
                FROM conversation_messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()
        items = []
        for row in reversed(rows):
            item = dict(row)
            item["citations"] = json.loads(item.pop("citations_json") or "[]")
            item["trace"] = json.loads(item.pop("trace_json") or "{}")
            items.append(item)
        return items

    def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
        return dict(row) if row else None

    def delete_conversation(self, conversation_id: str) -> bool:
        with self.db.connect() as connection:
            connection.execute("DELETE FROM conversation_messages WHERE conversation_id = ?", (conversation_id,))
            cursor = connection.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
        return cursor.rowcount > 0
