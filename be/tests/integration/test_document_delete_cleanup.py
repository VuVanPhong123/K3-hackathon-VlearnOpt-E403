from app.repositories.database import Database
from app.repositories.document_repository import DocumentRepository
from app.schemas import DocumentMetadata


def test_document_delete_cleanup(tmp_path) -> None:
    db = Database(tmp_path / "test.db")
    repo = DocumentRepository(db)
    repo.upsert_document(DocumentMetadata(id="d1", original_filename="x.pdf", stored_filename="x.pdf", checksum_sha256="sha", page_count=1, size_bytes=1, uploaded_at="now"))
    repo.delete_document_data("d1")
    assert repo.get_document("d1") is None
