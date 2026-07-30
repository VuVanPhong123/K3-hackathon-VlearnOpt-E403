from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from app.repositories.database import Database, database
from app.schemas import DocumentMetadata


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class DocumentRepository:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or database

    def upsert_document(self, metadata: DocumentMetadata) -> None:
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    id, original_filename, stored_filename, checksum_sha256, version,
                    page_count, size_bytes, uploaded_at, status, processing_error,
                    text_page_count, visual_only_page_count, chunk_count, indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    original_filename=excluded.original_filename,
                    stored_filename=excluded.stored_filename,
                    checksum_sha256=excluded.checksum_sha256,
                    version=excluded.version,
                    page_count=excluded.page_count,
                    size_bytes=excluded.size_bytes,
                    uploaded_at=excluded.uploaded_at,
                    status=excluded.status,
                    processing_error=excluded.processing_error,
                    text_page_count=excluded.text_page_count,
                    visual_only_page_count=excluded.visual_only_page_count,
                    chunk_count=excluded.chunk_count,
                    indexed_at=excluded.indexed_at
                """,
                (
                    metadata.id,
                    metadata.original_filename,
                    metadata.stored_filename,
                    metadata.checksum_sha256,
                    metadata.version,
                    metadata.page_count,
                    metadata.size_bytes,
                    metadata.uploaded_at,
                    metadata.status,
                    metadata.processing_error,
                    metadata.text_page_count,
                    metadata.visual_only_page_count,
                    metadata.chunk_count,
                    metadata.indexed_at,
                ),
            )

    def get_document(self, document_id: str) -> DocumentMetadata | None:
        with self.db.connect() as connection:
            row = connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return DocumentMetadata(**dict(row)) if row else None

    def list_documents(self) -> list[DocumentMetadata]:
        with self.db.connect() as connection:
            rows = connection.execute("SELECT * FROM documents ORDER BY uploaded_at DESC").fetchall()
        return [DocumentMetadata(**dict(row)) for row in rows]

    def find_by_checksum(self, checksum_sha256: str) -> DocumentMetadata | None:
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM documents WHERE checksum_sha256 = ? ORDER BY uploaded_at DESC LIMIT 1",
                (checksum_sha256,),
            ).fetchone()
        return DocumentMetadata(**dict(row)) if row else None

    def update_status(self, document_id: str, status: str, error: str | None = None) -> None:
        with self.db.connect() as connection:
            connection.execute(
                "UPDATE documents SET status = ?, processing_error = ? WHERE id = ?",
                (status, error, document_id),
            )

    def update_index_stats(
        self,
        document_id: str,
        *,
        status: str,
        text_page_count: int,
        visual_only_page_count: int,
        chunk_count: int,
        indexed_at: str | None = None,
        error: str | None = None,
    ) -> None:
        with self.db.connect() as connection:
            connection.execute(
                """
                UPDATE documents
                SET status = ?, processing_error = ?, text_page_count = ?,
                    visual_only_page_count = ?, chunk_count = ?, indexed_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    error,
                    text_page_count,
                    visual_only_page_count,
                    chunk_count,
                    indexed_at or now_iso(),
                    document_id,
                ),
            )

    def set_job(self, document_id: str, status: str, stage: str, progress: int, error: str | None = None) -> None:
        with self.db.connect() as connection:
            connection.execute(
                """
                INSERT INTO ingestion_jobs(document_id, status, stage, progress, error, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    status=excluded.status, stage=excluded.stage, progress=excluded.progress,
                    error=excluded.error, updated_at=excluded.updated_at
                """,
                (document_id, status, stage, progress, error, now_iso()),
            )

    def get_job(self, document_id: str) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT status, stage, progress, error FROM ingestion_jobs WHERE document_id = ?",
                (document_id,),
            ).fetchone()
        return dict(row) if row else None

    def delete_document_data(self, document_id: str) -> None:
        with self.db.connect() as connection:
            for table in [
                "pages",
                "sections",
                "chunks",
                "ingestion_jobs",
                "conversation_messages",
                "conversations",
                "documents",
            ]:
                column = "conversation_id" if table == "conversation_messages" else "document_id"
                if table == "conversation_messages":
                    conversation_ids = [
                        row["conversation_id"]
                        for row in connection.execute(
                            "SELECT conversation_id FROM conversations WHERE document_id = ?",
                            (document_id,),
                        ).fetchall()
                    ]
                    for conversation_id in conversation_ids:
                        connection.execute("DELETE FROM conversation_messages WHERE conversation_id = ?", (conversation_id,))
                    continue
                if table == "documents":
                    connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
                    continue
                connection.execute(f"DELETE FROM {table} WHERE {column} = ?", (document_id,))

    def replace_pages(self, document_id: str, pages: list[dict[str, Any]]) -> None:
        with self.db.connect() as connection:
            connection.execute("DELETE FROM pages WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO pages(
                    document_id, document_version, page_number, raw_text, blocks_json,
                    width, height, has_text, text_length, requires_vision
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        page["document_id"],
                        page["document_version"],
                        page["page_number"],
                        page["raw_text"],
                        json.dumps(page["blocks"], ensure_ascii=False),
                        page["width"],
                        page["height"],
                        int(page["has_text"]),
                        page["text_length"],
                        int(page["requires_vision"]),
                    )
                    for page in pages
                ],
            )

    def get_page(self, document_id: str, page_number: int) -> dict[str, Any] | None:
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM pages WHERE document_id = ? AND page_number = ?",
                (document_id, page_number),
            ).fetchone()
        if not row:
            return None
        item = dict(row)
        item["blocks"] = json.loads(item.pop("blocks_json") or "[]")
        item["has_text"] = bool(item["has_text"])
        item["requires_vision"] = bool(item["requires_vision"])
        return item

    def list_pages(self, document_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM pages WHERE document_id = ? ORDER BY page_number",
                (document_id,),
            ).fetchall()
        pages = []
        for row in rows:
            item = dict(row)
            item["blocks"] = json.loads(item.pop("blocks_json") or "[]")
            item["has_text"] = bool(item["has_text"])
            item["requires_vision"] = bool(item["requires_vision"])
            pages.append(item)
        return pages

    def replace_sections(self, document_id: str, sections: list[dict[str, Any]]) -> None:
        with self.db.connect() as connection:
            connection.execute("DELETE FROM sections WHERE document_id = ?", (document_id,))
            connection.executemany(
                """
                INSERT INTO sections(section_id, document_id, document_version, title, start_page, end_page)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        section["section_id"],
                        section["document_id"],
                        section["document_version"],
                        section["title"],
                        section["start_page"],
                        section["end_page"],
                    )
                    for section in sections
                ],
            )

    def list_sections(self, document_id: str) -> list[dict[str, Any]]:
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM sections WHERE document_id = ? ORDER BY start_page",
                (document_id,),
            ).fetchall()
        return [dict(row) for row in rows]
