from __future__ import annotations

import hashlib
import logging
import math
import threading
from typing import Protocol

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, text: str) -> list[float]:
        ...


class HashEmbeddingProvider:
    def __init__(self, dimensions: int = 96) -> None:
        self.dimensions = dimensions

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = text.lower().split()
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:2], "big") % self.dimensions
            sign = 1.0 if digest[2] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class HuggingFaceEmbeddingProvider:
    _model = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self.model_name = settings.embedding_model
        self.batch_size = settings.embedding_batch_size
        self.device = settings.embedding_device
        self.cache_dir = settings.embedding_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _load_model(self):
        with self._lock:
            if self.__class__._model is None:
                from sentence_transformers import SentenceTransformer

                self.__class__._model = SentenceTransformer(
                    self.model_name,
                    device=self.device,
                    cache_folder=str(self.cache_dir),
                )
            return self.__class__._model

    def _needs_e5_prefix(self) -> bool:
        return "e5" in self.model_name.lower()

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        payload = [f"passage: {text}" if self._needs_e5_prefix() else text for text in texts]
        vectors = model.encode(payload, batch_size=self.batch_size, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    def embed_query(self, text: str) -> list[float]:
        model = self._load_model()
        payload = f"query: {text}" if self._needs_e5_prefix() else text
        vector = model.encode([payload], batch_size=1, normalize_embeddings=True)[0]
        return vector.tolist()


class EmbeddingService:
    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        self.provider = provider

    def _provider(self) -> EmbeddingProvider:
        if self.provider:
            return self.provider
        if settings.embedding_provider == "huggingface":
            try:
                self.provider = HuggingFaceEmbeddingProvider()
                return self.provider
            except Exception as exc:
                return self._fallback_or_raise(exc)
        self.provider = HashEmbeddingProvider()
        return self.provider

    def _fallback_or_raise(self, exc: Exception) -> HashEmbeddingProvider:
        if not settings.embedding_fallback_enabled:
            raise exc
        logger.warning(
            "HuggingFace embedding failed; falling back to hash embeddings",
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        self.provider = HashEmbeddingProvider()
        return self.provider

    def embed_chunks(self, chunks: list[dict]) -> dict[str, list[float]]:
        try:
            vectors = self._provider().embed_passages([chunk["text"] for chunk in chunks])
        except Exception as exc:
            self.provider = self._fallback_or_raise(exc)
            vectors = self.provider.embed_passages([chunk["text"] for chunk in chunks])
        return {chunk["chunk_id"]: vector for chunk, vector in zip(chunks, vectors)}

    def embed_query(self, query: str) -> list[float]:
        try:
            return self._provider().embed_query(query)
        except Exception as exc:
            self.provider = self._fallback_or_raise(exc)
            return self.provider.embed_query(query)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size])) or 1.0
    right_norm = math.sqrt(sum(value * value for value in right[:size])) or 1.0
    return dot / (left_norm * right_norm)
