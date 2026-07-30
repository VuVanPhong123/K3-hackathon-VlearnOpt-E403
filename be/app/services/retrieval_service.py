from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.repositories.chunk_repository import ChunkRepository
from app.services.embedding_service import EmbeddingService, cosine_similarity
from app.services.lexical_search_service import LexicalSearchService
from app.services.reranker_service import OptionalReranker
from app.services.text_utils import snippet, tokenize


@dataclass
class RetrievalResult:
    chunk: dict
    score: float
    debug: dict


class RetrievalService:
    def __init__(
        self,
        chunk_repository: ChunkRepository | None = None,
        embedding_service: EmbeddingService | None = None,
    ) -> None:
        self.chunk_repository = chunk_repository or ChunkRepository()
        self.embedding_service = embedding_service or EmbeddingService()
        self.lexical = LexicalSearchService()
        self.reranker = OptionalReranker()

    def search(self, document_id: str, query: str, top_k: int | None = None) -> list[RetrievalResult]:
        chunks = self.chunk_repository.list_chunks(document_id)
        if not chunks:
            return []
        final_top_k = top_k or settings.retrieval_final_top_k
        lexical_hits = self.lexical.search(query, chunks, settings.retrieval_lexical_top_k)
        lexical_rank = {hit.chunk_id: hit.rank for hit in lexical_hits}
        query_vector = self.embedding_service.embed_query(query)
        dense_ranked = sorted(
            (
                (chunk["chunk_id"], cosine_similarity(query_vector, chunk.get("embedding", [])))
                for chunk in chunks
            ),
            key=lambda item: item[1],
            reverse=True,
        )[: settings.retrieval_dense_top_k]
        dense_rank = {chunk_id: index + 1 for index, (chunk_id, _) in enumerate(dense_ranked)}
        dense_scores = dict(dense_ranked)
        chunk_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
        candidate_ids = set(lexical_rank) | set(dense_rank)
        query_tokens = set(tokenize(query))
        fused: list[RetrievalResult] = []
        for chunk_id in candidate_ids:
            bm25_position = lexical_rank.get(chunk_id)
            dense_position = dense_rank.get(chunk_id)
            chunk_tokens = set(tokenize(chunk_by_id[chunk_id]["text"]))
            lexical_overlap = len(query_tokens & chunk_tokens) / max(1, len(query_tokens))
            score = 0.0
            if bm25_position:
                score += 1.0 / (60 + bm25_position) + 0.01
            if dense_position:
                score += 1.0 / (60 + dense_position)
            score += lexical_overlap * 0.05
            normalized_score = min(1.0, score * 32)
            if normalized_score < settings.retrieval_min_score:
                continue
            fused.append(
                RetrievalResult(
                    chunk=chunk_by_id[chunk_id],
                    score=normalized_score,
                    debug={
                        "chunk_id": chunk_id,
                        "bm25_rank": bm25_position,
                        "dense_rank": dense_position,
                        "dense_score": dense_scores.get(chunk_id, 0.0),
                        "fused_score": normalized_score,
                    },
                )
            )
        fused.sort(key=lambda item: item.score, reverse=True)
        if not settings.enable_reranker:
            return fused[:final_top_k]
        reranked_chunks = self.reranker.rerank(query, [item.chunk for item in fused[: settings.retrieval_fused_top_k]])
        rank_map = {chunk["chunk_id"]: index for index, chunk in enumerate(reranked_chunks)}
        fused.sort(key=lambda item: rank_map.get(item.chunk["chunk_id"], 999))
        return fused[:final_top_k]

    def debug_search(self, document_id: str, query: str, top_k: int) -> list[dict]:
        return [
            {
                "chunk_id": result.chunk["chunk_id"],
                "page_number": result.chunk["page_number"],
                "heading": result.chunk.get("heading"),
                "snippet": snippet(result.chunk["text"]),
                "score": result.score,
                "debug": result.debug,
            }
            for result in self.search(document_id, query, top_k)
        ]
