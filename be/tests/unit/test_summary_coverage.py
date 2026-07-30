from app.repositories.chunk_repository import ChunkRepository
from app.repositories.database import Database
from app.repositories.document_repository import DocumentRepository
from app.repositories.summary_repository import SummaryRepository
from app.schemas import DocumentMetadata
from app.services.summary_service import SummaryService


def test_summary_covers_all_sections(tmp_path) -> None:
    db = Database(tmp_path / "test.db")
    doc_repo = DocumentRepository(db)
    chunk_repo = ChunkRepository(db)
    summary_repo = SummaryRepository(db)
    doc_repo.upsert_document(
        DocumentMetadata(
            id="d1",
            original_filename="a.pdf",
            stored_filename="a.pdf",
            checksum_sha256="sha",
            page_count=2,
            size_bytes=1,
            uploaded_at="now",
            status="READY",
        )
    )
    doc_repo.replace_sections("d1", [
        {"section_id": "s1", "document_id": "d1", "document_version": 1, "title": "A", "start_page": 1, "end_page": 1},
        {"section_id": "s2", "document_id": "d1", "document_version": 1, "title": "B", "start_page": 2, "end_page": 2},
    ])
    chunk_repo.replace_chunks("d1", [
        {"chunk_id": "c1", "document_id": "d1", "document_version": 1, "page_number": 1, "section_id": "s1", "heading": "A", "text": "alpha", "normalized_text": "alpha", "content_type": "text", "block_indexes": [], "bbox": [], "token_estimate": 1, "embedding": []},
        {"chunk_id": "c2", "document_id": "d1", "document_version": 1, "page_number": 2, "section_id": "s2", "heading": "B", "text": "beta", "normalized_text": "beta", "content_type": "text", "block_indexes": [], "bbox": [], "token_estimate": 1, "embedding": []},
    ])
    result = SummaryService(doc_repo, chunk_repo, summary_repo).summarize("d1")
    assert all(item["covered"] for item in result["coverage"])
    assert len(result["coverage"]) == 2
