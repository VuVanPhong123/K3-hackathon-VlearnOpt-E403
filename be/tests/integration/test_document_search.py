from app.repositories.chunk_repository import ChunkRepository
from app.repositories.database import Database
from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.retrieval_service import RetrievalService


def test_document_search(tmp_path) -> None:
    db = Database(tmp_path / "test.db")
    repo = ChunkRepository(db)
    repo.replace_chunks("d1", [
        {"chunk_id": "c1", "document_id": "d1", "document_version": 1, "page_number": 3, "section_id": "s", "heading": "Retrieval", "text": "Hybrid retrieval combines BM25 and dense search.", "normalized_text": "hybrid retrieval combines bm25 and dense search.", "content_type": "text", "block_indexes": [], "bbox": [], "token_estimate": 8, "embedding": []}
    ])
    results = RetrievalService(repo, EmbeddingService(HashEmbeddingProvider())).search("d1", "dense search", top_k=1)
    assert results and results[0].chunk["chunk_id"] == "c1"
