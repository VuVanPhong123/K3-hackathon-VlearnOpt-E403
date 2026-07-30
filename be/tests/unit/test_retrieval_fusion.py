from app.repositories.chunk_repository import ChunkRepository
from app.repositories.database import Database
from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.retrieval_service import RetrievalService


def test_hybrid_retrieval_finds_required_page(tmp_path) -> None:
    db = Database(tmp_path / "test.db")
    repo = ChunkRepository(db)
    chunks = [
        {
            "chunk_id": "c1",
            "document_id": "d1",
            "document_version": 1,
            "page_number": 3,
            "section_id": "s1",
            "heading": "Retrieval",
            "text": "Hybrid retrieval uses lexical BM25 and dense embedding fusion.",
            "normalized_text": "hybrid retrieval uses lexical bm25 and dense embedding fusion.",
            "content_type": "text",
            "block_indexes": [0],
            "bbox": [0, 0, 1, 1],
            "token_estimate": 12,
            "embedding": [1.0, 0.0],
        },
        {
            "chunk_id": "c2",
            "document_id": "d1",
            "document_version": 1,
            "page_number": 7,
            "section_id": "s2",
            "heading": "Other",
            "text": "Unrelated material",
            "normalized_text": "unrelated material",
            "content_type": "text",
            "block_indexes": [0],
            "bbox": [0, 0, 1, 1],
            "token_estimate": 3,
            "embedding": [0.0, 1.0],
        },
    ]
    repo.replace_chunks("d1", chunks)
    service = RetrievalService(repo, EmbeddingService(HashEmbeddingProvider()))
    results = service.search("d1", "BM25 dense retrieval", top_k=1)
    assert results[0].chunk["page_number"] == 3
