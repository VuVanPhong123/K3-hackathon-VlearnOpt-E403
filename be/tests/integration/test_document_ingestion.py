from app.repositories.chunk_repository import ChunkRepository
from app.repositories.database import Database
from app.repositories.document_repository import DocumentRepository
from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.ingestion_service import IngestionService
from app.schemas import DocumentMetadata
from tests.fixtures import create_fixture_pdf


def test_document_ingestion(tmp_path) -> None:
    db = Database(tmp_path / "test.db")
    doc_repo = DocumentRepository(db)
    chunk_repo = ChunkRepository(db)
    pdf = create_fixture_pdf(tmp_path / "fixture.pdf")
    doc_repo.upsert_document(
        DocumentMetadata(
            id="d1",
            original_filename="fixture.pdf",
            stored_filename="fixture.pdf",
            checksum_sha256="sha",
            page_count=9,
            size_bytes=pdf.stat().st_size,
            uploaded_at="now",
            status="UPLOADED",
        )
    )
    IngestionService(doc_repo, chunk_repo, EmbeddingService(HashEmbeddingProvider())).process_document("d1", pdf)
    assert doc_repo.get_document("d1").status == "READY"
    assert len(chunk_repo.list_chunks("d1")) >= 8
