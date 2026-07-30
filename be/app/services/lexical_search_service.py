from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.services.text_utils import search_normalize, snippet, tokenize


@dataclass
class LexicalHit:
    chunk_id: str
    score: float
    rank: int


class LexicalSearchService:
    def search(self, query: str, chunks: list[dict], top_k: int) -> list[LexicalHit]:
        if not query.strip() or not chunks:
            return []
        try:
            return self._bm25_search(query, chunks, top_k)
        except Exception:
            return self._overlap_search(query, chunks, top_k)

    def _bm25_search(self, query: str, chunks: list[dict], top_k: int) -> list[LexicalHit]:
        from rank_bm25 import BM25Okapi

        corpus = [tokenize(chunk["text"]) for chunk in chunks]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(tokenize(query))
        ranked = sorted(
            ((chunks[index]["chunk_id"], float(score)) for index, score in enumerate(scores)),
            key=lambda item: item[1],
            reverse=True,
        )
        return [LexicalHit(chunk_id=chunk_id, score=score, rank=index + 1) for index, (chunk_id, score) in enumerate(ranked[:top_k])]

    def _overlap_search(self, query: str, chunks: list[dict], top_k: int) -> list[LexicalHit]:
        query_tokens = Counter(tokenize(query))
        results: list[tuple[str, float]] = []
        for chunk in chunks:
            chunk_tokens = Counter(tokenize(chunk["text"]))
            overlap = sum(min(count, chunk_tokens[token]) for token, count in query_tokens.items())
            fuzzy_bonus = self._fuzzy_bonus(query, chunk["text"])
            score = overlap + fuzzy_bonus
            if score > 0:
                results.append((chunk["chunk_id"], float(score)))
        ranked = sorted(results, key=lambda item: item[1], reverse=True)
        return [LexicalHit(chunk_id=chunk_id, score=score, rank=index + 1) for index, (chunk_id, score) in enumerate(ranked[:top_k])]

    @staticmethod
    def _fuzzy_bonus(query: str, text: str) -> float:
        try:
            from rapidfuzz import fuzz

            return max(0.0, (fuzz.partial_ratio(search_normalize(query), search_normalize(snippet(text, 800))) - 65) / 35)
        except Exception:
            return 0.0
