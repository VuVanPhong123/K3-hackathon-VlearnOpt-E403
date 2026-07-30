from __future__ import annotations

from app.config import settings


class Reranker:
    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        return chunks


class OptionalReranker(Reranker):
    def __init__(self) -> None:
        self.enabled = settings.enable_reranker
        self.model_name = settings.reranker_model
        self._model = None

    def rerank(self, query: str, chunks: list[dict]) -> list[dict]:
        if not self.enabled or not chunks:
            return chunks
        try:
            model = self._load_model()
            pairs = [[query, chunk["text"]] for chunk in chunks[: settings.reranker_top_n]]
            scores = model.predict(pairs)
            rescored = [
                {**chunk, "rerank_score": float(score)}
                for chunk, score in zip(chunks[: settings.reranker_top_n], scores)
            ]
            rescored.sort(key=lambda item: item["rerank_score"], reverse=True)
            return rescored[: settings.reranker_final_n]
        except Exception:
            return chunks

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name)
        return self._model
