from __future__ import annotations

import json
from typing import Any

from app.repositories.database import Database, database


class ChunkRepository:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or database

    def replace_chunks(self, document_id: str, chunks: list[dict[str, Any]]) -> None:
        with self.db.connect() as connection:
            connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO chunks(
                    chunk_id, document_id, document_version, page_number, section_id,
                    heading, text, normalized_text, content_type, block_indexes_json,
                    bbox_json, previous_chunk_id, next_chunk_id, token_estimate,
                    embedding_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk["chunk_id"],
                        chunk["document_id"],
                        chunk["document_version"],
                        chunk["page_number"],
                        chunk.get("section_id"),
                        chunk.get("heading"),
                        chunk["text"],
                        chunk["normalized_text"],
                        chunk.get("content_type", "text"),
                        json.dumps(chunk.get("block_indexes", [])),
                        json.dumps(chunk.get("bbox", [])),
                        chunk.get("previous_chunk_id"),
                        chunk.get("next_chunk_id"),
                        chunk.get("token_estimate", 0),
                        json.dumps(chunk.get("embedding", [])),
                    )
                    for chunk in chunks
                ],
            )

    def list_chunks(self, document_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM chunks WHERE document_id = ? ORDER BY page_number, chunk_id",
                (document_id,),
            ).fetchall()
        return [self._row_to_chunk(row) for row in rows]

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            row = connection.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,)).fetchone()
        return self._row_to_chunk(row) if row else None

    def update_embeddings(self, embeddings: dict[str, list[float]]) -> None:
        with self.db.connect() as connection:
            connection.executemany(
                "UPDATE chunks SET embedding_json = ? WHERE chunk_id = ?",
                [(json.dumps(vector), chunk_id) for chunk_id, vector in embeddings.items()],
            )

    @staticmethod
    def _row_to_chunk(row: Any) -> dict[str, Any]:
        item = dict(row)
        item["block_indexes"] = json.loads(item.pop("block_indexes_json") or "[]")
        item["bbox"] = json.loads(item.pop("bbox_json") or "[]")
        item["embedding"] = json.loads(item.pop("embedding_json") or "[]")
        return item
