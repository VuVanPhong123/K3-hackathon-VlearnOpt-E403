from app.services.embedding_service import HashEmbeddingProvider


def test_hash_embedding_is_deterministic() -> None:
    provider = HashEmbeddingProvider()
    assert provider.embed_query("rag citation") == provider.embed_query("rag citation")
