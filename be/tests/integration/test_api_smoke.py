from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.routers import chat_v2, documents
from app.services.answer_service import AnswerService
from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.ingestion_service import IngestionService
from app.services.orchestration_service import OrchestrationService
from app.services.provider_gateway import ProviderGateway
from app.services.providers.base import ProviderResult
from tests.fixtures import create_fixture_pdf


class RecordingProvider:
    def __init__(self) -> None:
        self.calls = []

    async def generate(self, *, system_prompt: str, messages: list[dict[str, str]]) -> ProviderResult:
        self.calls.append({"system_prompt": system_prompt, "messages": messages})
        return ProviderResult(
            text="Câu trả lời tích hợp từ provider giả.",
            provider="openai",
            model="fake-openai",
        )

    async def generate_multimodal(
        self,
        *,
        system_prompt: str,
        text_prompt: str,
        image_bytes: bytes,
        mime_type: str,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResult:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": [*(history or []), {"role": "user", "content": text_prompt}],
                "image_bytes": image_bytes,
                "mime_type": mime_type,
            }
        )
        return ProviderResult(
            text="Câu trả lời tích hợp từ ảnh trang.",
            provider="openai",
            model="fake-openai-vision",
        )


def test_api_smoke_upload_general_page_chat_and_delete(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", "test-key")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "primary_text_provider", "openai")

    documents.ingestion_service = IngestionService(
        documents.document_service.repository,
        documents.retrieval_service.chunk_repository,
        EmbeddingService(HashEmbeddingProvider()),
    )
    provider = RecordingProvider()
    gateway = ProviderGateway(
        openai_factory=lambda: provider,
        gemini_factory=lambda: provider,
    )
    monkeypatch.setattr(
        chat_v2,
        "orchestration_service",
        OrchestrationService(
            answer_service=AnswerService(gateway),
            document_service=documents.document_service,
            page_context_service=documents.page_context_service,
        ),
    )

    client = TestClient(app)
    assert client.get("/api/health").status_code == 200

    pdf = create_fixture_pdf(tmp_path / "fixture.pdf")
    with fitz.open(pdf) as fixture:
        fixture[0].insert_text((36, 36), f"Run: {tmp_path.name}")
        fixture.saveIncr()
    with pdf.open("rb") as handle:
        upload = client.post(
            "/api/documents",
            files={"file": ("fixture.pdf", handle, "application/pdf")},
        )
    assert upload.status_code == 200
    document_id = upload.json()["id"]

    general = client.post(
        "/api/v2/chat",
        json={
            "message": "Xin chào Tutor",
            "document_id": None,
            "context": {"attached_pages": []},
            "answer_mode": "allow_general_knowledge",
        },
    )
    assert general.status_code == 200
    assert general.json()["citations"] == []

    page = client.post(
        "/api/v2/chat",
        json={
            "message": "Trang này nói gì?",
            "document_id": document_id,
            "context": {"attached_pages": [3]},
            "answer_mode": "document_only",
        },
    )
    assert page.status_code == 200
    assert page.json()["citations"][0]["page_number"] == 3
    assert "Trang PDF: 3" in provider.calls[-1]["messages"][-1]["content"]
    assert provider.calls[-1]["image_bytes"].startswith(b"\x89PNG")

    monkeypatch.setattr(settings, "openai_api_key", "")
    old_chat = client.post("/api/chat", json={"message": "hello", "history": []})
    assert old_chat.status_code == 503

    delete = client.delete(f"/api/documents/{document_id}")
    assert delete.status_code == 200
