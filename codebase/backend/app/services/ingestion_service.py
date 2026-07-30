from __future__ import annotations

import logging
from pathlib import Path

from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository, now_iso
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.page_extraction_service import PageExtractionService
from app.services.section_service import SectionService

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        document_repository: DocumentRepository | None = None,
        chunk_repository: ChunkRepository | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.document_repository = document_repository or DocumentRepository()
        self.chunk_repository = chunk_repository or ChunkRepository()
        self.embedding_service = embedding_service or EmbeddingService()
        self.page_extractor = PageExtractionService()
        self.section_service = SectionService()
        self.chunking_service = ChunkingService()

    def process_document(self, document_id: str, pdf_path: str | Path) -> None:
        path = Path(pdf_path)
        metadata = self.document_repository.get_document(document_id)
        if not metadata:
            return
        try:
            self.document_repository.update_status(document_id, "PROCESSING")
            self.document_repository.set_job(document_id, "PROCESSING", "extracting_pages", 10)
            pages = self.page_extractor.extract(path, metadata.id, metadata.version)
            self.document_repository.replace_pages(document_id, pages)

            self.document_repository.set_job(document_id, "PROCESSING", "detecting_sections", 35)
            sections = self.section_service.detect_sections(metadata.id, metadata.version, pages)
            self.document_repository.replace_sections(document_id, sections)

            self.document_repository.set_job(document_id, "PROCESSING", "chunking", 50)
            chunks = self.chunking_service.create_chunks(metadata.id, metadata.version, pages, sections)

            self.document_repository.set_job(document_id, "PROCESSING", "embedding", 70)
            embeddings = self.embedding_service.embed_chunks(chunks)
            for chunk in chunks:
                chunk["embedding"] = embeddings.get(chunk["chunk_id"], [])
            self.chunk_repository.replace_chunks(document_id, chunks)

            text_page_count = sum(1 for page in pages if page["has_text"])
            visual_only_page_count = sum(1 for page in pages if page["requires_vision"])
            self.document_repository.update_index_stats(
                document_id,
                status="READY",
                text_page_count=text_page_count,
                visual_only_page_count=visual_only_page_count,
                chunk_count=len(chunks),
                indexed_at=now_iso(),
            )
            self.document_repository.set_job(document_id, "READY", "ready", 100)
        except Exception as exc:
            logger.exception("Document ingestion failed for %s", document_id)
            self.document_repository.update_index_stats(
                document_id,
                status="FAILED",
                text_page_count=0,
                visual_only_page_count=0,
                chunk_count=0,
                error=str(exc),
            )
            self.document_repository.set_job(document_id, "FAILED", "failed", 100, str(exc))
