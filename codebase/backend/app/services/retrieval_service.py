from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.repositories.chunk_repository import ChunkRepository
from app.services.embedding_service import EmbeddingService, cosine_similarity
from app.services.lexical_search_service import LexicalSearchService
from app.services.query_planner import QueryVariant, chunk_search_text, normalize_phrase, QueryPlanner
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
        self.query_planner = QueryPlanner()

    def search(self, document_id: str, query: str, top_k: int | None = None) -> list[RetrievalResult]:
        chunks = self.chunk_repository.list_chunks(document_id)
        if not chunks:
            return []
        final_top_k = top_k or settings.retrieval_final_top_k
        plan = self.query_planner.plan_for_retrieval(query, chunks)
        fused_by_chunk: dict[str, RetrievalResult] = {}

        for variant in plan.variants:
            for result in self._search_variant(variant, chunks):
                if plan.is_term_query and not self._term_match_allowed(result.chunk, plan.target_term):
                    continue
                score = self._score_with_boosts(result, variant, plan.target_term)
                debug = {
                    **plan.debug(),
                    **result.debug,
                    "query_variant": variant.text,
                    "query_variant_kind": variant.kind,
                    "variant_weight": variant.weight,
                    "boosted_score": score,
                    "heading_match": self._heading_match(result.chunk, plan.target_term),
                    "phrase_match": self._phrase_match(result.chunk, plan.target_term),
                }
                existing = fused_by_chunk.get(result.chunk["chunk_id"])
                if existing is None or score > existing.score:
                    fused_by_chunk[result.chunk["chunk_id"]] = RetrievalResult(
                        chunk=result.chunk,
                        score=score,
                        debug=debug,
                    )

        fused = list(fused_by_chunk.values())
        if plan.is_term_query and not fused:
            return []
        fused.sort(key=lambda item: (-item.score, item.chunk["chunk_id"]))
        selected = self._select_distinct_evidence(fused, final_top_k)
        if not settings.enable_reranker:
            return selected

        reranked_chunks = self.reranker.rerank(query, [item.chunk for item in fused[: settings.retrieval_fused_top_k]])
        rank_map = {chunk["chunk_id"]: index for index, chunk in enumerate(reranked_chunks)}
        fused.sort(key=lambda item: rank_map.get(item.chunk["chunk_id"], 999))
        return self._select_distinct_evidence(fused, final_top_k)

    def _search_variant(self, variant: QueryVariant, chunks: list[dict]) -> list[RetrievalResult]:
        query = variant.text
        lexical_hits = self.lexical.search(query, chunks, settings.retrieval_lexical_top_k)
        lexical_rank = {hit.chunk_id: hit.rank for hit in lexical_hits}
        lexical_scores = {hit.chunk_id: hit.score for hit in lexical_hits}
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
        results: list[RetrievalResult] = []
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
            # RRF scores are small by design. A factor of 32 saturated almost
            # every candidate at 1.0 and erased the relevance ordering.
            normalized_score = min(1.0, score * 10)
            if normalized_score < settings.retrieval_min_score:
                continue
            results.append(
                RetrievalResult(
                    chunk=chunk_by_id[chunk_id],
                    score=normalized_score,
                    debug={
                        "chunk_id": chunk_id,
                        "query_tokens": sorted(query_tokens),
                        "bm25_rank": bm25_position,
                        "bm25_score": lexical_scores.get(chunk_id, 0.0),
                        "dense_rank": dense_position,
                        "dense_score": dense_scores.get(chunk_id, 0.0),
                        "lexical_overlap": lexical_overlap,
                        "fused_score": normalized_score,
                    },
                )
            )
        results.sort(key=lambda item: (-item.score, item.chunk["chunk_id"]))
        return results

    @staticmethod
    def _score_with_boosts(
        result: RetrievalResult,
        variant: QueryVariant,
        target_term: str | None,
    ) -> float:
        score = result.score * variant.weight
        if target_term:
            if RetrievalService._heading_match(result.chunk, target_term):
                score += 0.35
            elif RetrievalService._phrase_match(result.chunk, target_term):
                score += 0.25
        if variant.kind == "spelling_candidate":
            score *= 0.92
        return min(1.0, score)

    @staticmethod
    def _term_match_allowed(chunk: dict, target_term: str | None) -> bool:
        if not target_term:
            return False
        return RetrievalService._phrase_match(chunk, target_term)

    @staticmethod
    def _heading_match(chunk: dict, target_term: str | None) -> bool:
        if not target_term:
            return False
        needle = f" {normalize_phrase(target_term)} "
        return needle in f" {normalize_phrase(str(chunk.get('heading') or ''))} "

    @staticmethod
    def _phrase_match(chunk: dict, target_term: str | None) -> bool:
        if not target_term:
            return False
        needle = f" {normalize_phrase(target_term)} "
        return needle in f" {chunk_search_text(chunk)} "

    @staticmethod
    def _select_distinct_evidence(results: list[RetrievalResult], top_k: int) -> list[RetrievalResult]:
        selected: list[RetrievalResult] = []
        seen_pages: set[int] = set()
        seen_texts: set[str] = set()

        def add(result: RetrievalResult) -> None:
            text_key = normalize_phrase(snippet(result.chunk.get("text", ""), 220))
            if text_key in seen_texts:
                return
            seen_texts.add(text_key)
            selected.append(result)

        for result in results:
            page_number = int(result.chunk.get("page_number") or 0)
            if page_number in seen_pages:
                continue
            seen_pages.add(page_number)
            add(result)
            if len(selected) >= top_k:
                return selected
        for result in results:
            if len(selected) >= top_k:
                break
            if result not in selected:
                add(result)
        return selected
