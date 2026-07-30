from __future__ import annotations

import pytest

from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.query_planner import QueryPlanner, extract_term_query, normalize_phrase
from app.services.retrieval_service import RetrievalService


def _chunks() -> list[dict]:
    texts = [
        (
            "Encoder",
            "An encoder converts input tokens into contextual representations for a model.",
        ),
        (
            "Multi-head attention",
            "Multi-head attention uses several attention heads to learn complementary relationships.",
        ),
        (
            "RAG overview",
            "RAG retrieves document evidence before generating an answer with citations.",
        ),
        (
            "Prompt injection",
            "Prompt injection is an instruction attack that tries to override system rules.",
        ),
        (
            "Context window",
            "The context window is the amount of text a model can consider at once.",
        ),
        (
            "Reinforcement learning",
            "Reinforcement learning improves behavior from rewards.",
        ),
        (
            "Overfitting",
            "Overfitting happens when a model fits training data too closely.",
        ),
        (
            "Chuỗi cung ứng",
            "Chuỗi cung ứng mô tả dòng hàng hóa, tiền và thông tin giữa các bên.",
        ),
    ]
    provider = HashEmbeddingProvider()
    vectors = provider.embed_passages([text for _, text in texts])
    return [
        {
            "chunk_id": f"c{index}",
            "document_id": "d1",
            "page_number": index,
            "heading": heading,
            "text": text,
            "embedding": vector,
        }
        for index, ((heading, text), vector) in enumerate(zip(texts, vectors), start=1)
    ]


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("encoder là gì thế", "encoder"),
        ("Encoder nghĩa là gì?", "Encoder"),
        ("ENCODER LÀ GÌ", "ENCODER"),
        ("encoder la gi", "encoder"),
        ("giải thích encoder", "encoder"),
        ("giải thích giúp tôi cơ chế self attention", "cơ chế self attention"),
        ("prompt injection nghĩa là gì nhỉ", "prompt injection"),
        ("context window dùng để làm gì", "context window"),
        ("multi head attention hoạt động thế nào", "multi head attention"),
        ("RAG nghĩa là gì", "RAG"),
        ("what is retrieval augmented generation?", "retrieval augmented generation"),
        ("what does prompt injection mean", "prompt injection"),
        ("define context window", "context window"),
        ("explain tool calling", "tool calling"),
        ("tell me about RAG", "RAG"),
        ("how does multi head attention work", "multi head attention"),
    ],
)
def test_extract_term_queries_in_vietnamese_and_english(message: str, expected: str) -> None:
    assert extract_term_query(message) == expected


@pytest.mark.parametrize(
    "message",
    [
        "So sánh encoder và decoder.",
        "Trang 5 nói gì về encoder?",
        "Giải thích sơ đồ này.",
        "Tóm tắt phần nói về attention.",
        "Thuật ngữ nào liên quan đến retrieval trong tài liệu?",
        "RAG và citation được dùng để làm gì?",
    ],
)
def test_non_definition_queries_are_not_term_queries(message: str) -> None:
    assert extract_term_query(message) is None


def test_normalization_handles_case_accents_and_vietnamese_d() -> None:
    assert normalize_phrase("ENCODER LÀ GÌ") == "encoder la gi"
    assert normalize_phrase("hoạt động được không") == "hoat dong duoc khong"


def test_query_variants_are_deduplicated_limited_and_include_hyphen_variant() -> None:
    plan = QueryPlanner().plan_for_retrieval("multi head attention hoạt động thế nào", _chunks())

    texts = [variant.text for variant in plan.variants]
    assert texts == list(dict.fromkeys(texts))
    assert len(texts) <= 5
    assert "multi head attention" in texts
    assert "multi-head attention" in texts


def test_exact_term_is_not_fuzzy_rewritten() -> None:
    plan = QueryPlanner().plan_for_retrieval("encoder là gì", _chunks())

    assert plan.exact_phrase_match is True
    assert plan.selected_spelling_candidate is None
    assert plan.spelling_candidates == []


@pytest.mark.parametrize(
    ("message", "candidate"),
    [
        ("encodr là gì", "Encoder"),
        ("overfiting nghĩa là gì", "Overfitting"),
        ("reinforcemnt learning là gì", "Reinforcement learning"),
    ],
)
def test_typo_correction_uses_document_vocabulary(message: str, candidate: str) -> None:
    plan = QueryPlanner().plan_for_retrieval(message, _chunks())

    assert plan.selected_spelling_candidate == candidate
    assert any(item["candidate"] == candidate for item in plan.spelling_candidates)


@pytest.mark.parametrize("message", ["R là gì", "xyzabc là gì"])
def test_short_or_unrelated_terms_are_not_corrected(message: str) -> None:
    plan = QueryPlanner().plan_for_retrieval(message, _chunks())

    assert plan.selected_spelling_candidate is None


def test_truncated_prefix_is_not_silently_corrected_when_ambiguous() -> None:
    chunks = [
        {"chunk_id": "c1", "page_number": 1, "heading": "Encoder", "text": "Encoder maps input.", "embedding": []},
        {"chunk_id": "c2", "page_number": 2, "heading": "Encoding", "text": "Encoding maps symbols.", "embedding": []},
    ]
    plan = QueryPlanner().plan_for_retrieval("encod là gì", chunks)

    assert plan.selected_spelling_candidate is None


class InMemoryChunkRepository:
    def __init__(self, chunks: list[dict]) -> None:
        self.chunks = chunks

    def list_chunks(self, document_id: str) -> list[dict]:
        return self.chunks


def test_heading_and_phrase_exact_matches_are_boosted_and_debugged() -> None:
    results = RetrievalService(
        InMemoryChunkRepository(_chunks()),
        EmbeddingService(HashEmbeddingProvider()),
    ).search("d1", "prompt injection là gì", top_k=3)

    assert results[0].chunk["heading"] == "Prompt injection"
    assert results[0].debug["heading_match"] is True
    assert results[0].debug["phrase_match"] is True


def test_duplicate_chunks_are_merged_and_distinct_pages_are_preferred() -> None:
    provider = HashEmbeddingProvider()
    texts = [
        "RAG retrieves document evidence before generating an answer.",
        "RAG retrieves document evidence before generating an answer.",
        "RAG also returns citations to the pages used as evidence.",
    ]
    vectors = provider.embed_passages(texts)
    chunks = [
        {
            "chunk_id": f"c{index}",
            "document_id": "d1",
            "page_number": page,
            "heading": "RAG",
            "text": text,
            "embedding": vector,
        }
        for index, (page, text, vector) in enumerate(zip([1, 1, 2], texts, vectors), start=1)
    ]

    results = RetrievalService(InMemoryChunkRepository(chunks), EmbeddingService(provider)).search("d1", "RAG là gì", top_k=3)

    assert len({result.chunk["chunk_id"] for result in results}) == len(results)
    assert [result.chunk["page_number"] for result in results] == [1, 2]
