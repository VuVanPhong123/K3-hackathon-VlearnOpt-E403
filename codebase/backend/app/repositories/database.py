from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import settings


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.database_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL,
                    checksum_sha256 TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    page_count INTEGER NOT NULL DEFAULT 0,
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    uploaded_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'UPLOADED',
                    processing_error TEXT,
                    text_page_count INTEGER NOT NULL DEFAULT 0,
                    visual_only_page_count INTEGER NOT NULL DEFAULT 0,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    indexed_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_documents_checksum
                    ON documents(checksum_sha256);

                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    document_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    stage TEXT,
                    progress INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pages (
                    document_id TEXT NOT NULL,
                    document_version INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    raw_text TEXT NOT NULL,
                    blocks_json TEXT NOT NULL,
                    width REAL NOT NULL,
                    height REAL NOT NULL,
                    has_text INTEGER NOT NULL,
                    text_length INTEGER NOT NULL,
                    requires_vision INTEGER NOT NULL,
                    PRIMARY KEY(document_id, page_number)
                );

                CREATE TABLE IF NOT EXISTS sections (
                    section_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    document_version INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    start_page INTEGER NOT NULL,
                    end_page INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    document_version INTEGER NOT NULL,
                    page_number INTEGER NOT NULL,
                    section_id TEXT,
                    heading TEXT,
                    text TEXT NOT NULL,
                    normalized_text TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    block_indexes_json TEXT NOT NULL,
                    bbox_json TEXT NOT NULL,
                    previous_chunk_id TEXT,
                    next_chunk_id TEXT,
                    token_estimate INTEGER NOT NULL,
                    embedding_json TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_document
                    ON chunks(document_id, document_version);
                CREATE INDEX IF NOT EXISTS idx_chunks_page
                    ON chunks(document_id, page_number);

                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    document_id TEXT,
                    document_version INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    summary TEXT
                );

                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    citations_json TEXT NOT NULL DEFAULT '[]',
                    trace_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                """
            )


database = Database()
