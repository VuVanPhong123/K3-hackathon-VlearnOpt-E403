from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.routers import chat_v2, documents
from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.ingestion_service import IngestionService
from tests.fixtures import create_fixture_pdf


def test_api_smoke_upload_search_summary_chat_delete(tmp_path) -> None:
    documents.ingestion_service = IngestionService(
        documents.document_service.repository,
        documents.retrieval_service.chunk_repository,
        EmbeddingService(HashEmbeddingProvider()),
    )
    documents.retrieval_service.embedding_service = EmbeddingService(HashEmbeddingProvider())
    chat_v2.orchestration_service.context_resolver.retrieval_service.embedding_service = EmbeddingService(HashEmbeddingProvider())
    client = TestClient(app)
    assert client.get("/api/health").status_code == 200

    pdf = create_fixture_pdf(Path(tmp_path) / "fixture.pdf")
    with pdf.open("rb") as handle:
        upload = client.post("/api/documents", files={"file": ("fixture.pdf", handle, "application/pdf")})
    assert upload.status_code == 200
    document_id = upload.json()["id"]

    status = client.get(f"/api/documents/{document_id}/status")
    assert status.status_code == 200
    assert status.json()["status"] in {"READY", "PROCESSING", "UPLOADED"}

    search = client.get(f"/api/documents/{document_id}/search", params={"q": "hybrid retrieval", "top_k": 3})
    assert search.status_code == 200
    assert "results" in search.json()

    summary = client.get(f"/api/documents/{document_id}/summary", params={"type": "short"})
    assert summary.status_code == 200
    assert summary.json()["citations"]

    chat = client.post(
        "/api/v2/chat",
        json={
            "message": "hybrid retrieval la gi",
            "document_id": document_id,
            "context": {},
            "answer_mode": "document_only",
        },
    )
    assert chat.status_code == 200
    assert chat.json()["trace"]["intent"] in {"DOCUMENT_SEARCH", "PAGE_QA"}

    old_chat = client.post("/api/chat", json={"message": "hello", "history": []})
    assert old_chat.status_code in {200, 503}

    delete = client.delete(f"/api/documents/{document_id}")
    assert delete.status_code == 200
