from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.repositories.database import Database, database


class SummaryRepository:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or database

    @staticmethod
    def cache_key(document_id: str, checksum: str, version: int, summary_type: str, language: str) -> str:
        return f"{document_id}:{checksum}:{version}:{summary_type}:{language}"

    def get_summary(self, cache_key: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            row = connection.execute("SELECT * FROM summaries WHERE cache_key = ?", (cache_key,)).fetchone()
        if not row:
            return None
        item = dict(row)
        item["citations"] = json.loads(item.pop("citations_json") or "[]")
        item["coverage"] = json.loads(item.pop("coverage_json") or "[]")
        return item

    def save_summary(
        self,
        *,
        cache_key: str,
        document_id: str,
        document_version: int,
        checksum_sha256: str,
        summary_type: str,
        language: str,
        answer: str,
        citations: list[dict[str, Any]],
        coverage: list[dict[str, Any]],
    ) -> None:
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO summaries(
                    cache_key, document_id, document_version, checksum_sha256,
                    summary_type, language, answer, citations_json, coverage_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cache_key,
                    document_id,
                    document_version,
                    checksum_sha256,
                    summary_type,
                    language,
                    answer,
                    json.dumps(citations, ensure_ascii=False),
                    json.dumps(coverage, ensure_ascii=False),
                    datetime.now(UTC).isoformat(),
                ),
            )
