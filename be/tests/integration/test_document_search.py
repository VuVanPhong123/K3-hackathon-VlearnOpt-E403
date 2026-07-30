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


class InMemoryChunkRepository:
    def __init__(self, chunks: list[dict]) -> None:
        self.chunks = chunks

    def list_chunks(self, document_id: str) -> list[dict]:
        return self.chunks


def test_retrieval_preserves_relevance_order_instead_of_saturating_scores() -> None:
    texts = [
        "Visual-only attention map gồm một ma trận màu.",
        "Multi-head attention dùng nhiều attention head để học các quan hệ bổ sung.",
        "Kết luận về trợ lý grounded và bằng chứng.",
    ]
    embedding_provider = HashEmbeddingProvider()
    embeddings = embedding_provider.embed_passages(texts)
    chunks = [
        {
            "chunk_id": f"c{index}",
            "document_id": "d1",
            "page_number": index,
            "text": text,
            "embedding": embedding,
        }
        for index, (text, embedding) in enumerate(
            zip(texts, embeddings),
            start=1,
        )
    ]
    service = RetrievalService(
        InMemoryChunkRepository(chunks),
        EmbeddingService(embedding_provider),
    )

    results = service.search("d1", "Multi-head attention có tác dụng gì?", top_k=3)

    assert results[0].chunk["page_number"] == 2
    assert results[0].score > results[1].score


def test_retrieval_rejects_stopword_only_overlap() -> None:
    texts = [
        "Multi-head attention dùng nhiều attention head để học quan hệ bổ sung.",
        "Trợ lý grounded cần nói rõ khi thiếu bằng chứng.",
    ]
    embedding_provider = HashEmbeddingProvider()
    embeddings = embedding_provider.embed_passages(texts)
    chunks = [
        {
            "chunk_id": f"c{index}",
            "document_id": "d1",
            "page_number": index,
            "text": text,
            "embedding": embedding,
        }
        for index, (text, embedding) in enumerate(
            zip(texts, embeddings),
            start=1,
        )
    ]
    service = RetrievalService(
        InMemoryChunkRepository(chunks),
        EmbeddingService(embedding_provider),
    )

    results = service.search(
        "d1",
        "Quy trình phẫu thuật tim nội soi bằng robot được mô tả thế nào?",
        top_k=3,
    )

    assert results == []
