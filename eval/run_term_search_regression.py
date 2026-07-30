from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "codebase" / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BE))

from app.services.embedding_service import EmbeddingService, HashEmbeddingProvider
from app.services.query_planner import QueryPlanner
from app.services.retrieval_service import RetrievalService


TERM_FIXTURE = [
    ("Encoder", "An encoder converts input tokens into contextual representations for a model."),
    ("Multi-head attention", "Multi-head attention uses several attention heads to learn complementary relationships."),
    ("RAG overview", "RAG retrieves document evidence before generating an answer with citations."),
    ("Prompt injection", "Prompt injection is an instruction attack that tries to override system rules."),
    ("Context window", "The context window is the amount of text a model can consider at once."),
    ("Chuỗi cung ứng", "Chuỗi cung ứng mô tả dòng hàng hóa, tiền và thông tin giữa các bên."),
    ("Overfitting", "Overfitting happens when a model fits training data too closely."),
    ("Reinforcement learning", "Reinforcement learning improves behavior from rewards."),
    ("Encoder and encoding", "This page mentions both encoder and encoding for ambiguity checks."),
]


class FixtureChunkRepository:
    def __init__(self) -> None:
        provider = HashEmbeddingProvider()
        vectors = provider.embed_passages([text for _, text in TERM_FIXTURE])
        self.embedding_provider = provider
        self.chunks = [
            {
                "chunk_id": f"term-fixture-p{page}",
                "document_id": "term-fixture",
                "document_version": 1,
                "page_number": page,
                "heading": heading,
                "text": text,
                "embedding": vector,
            }
            for page, ((heading, text), vector) in enumerate(zip(TERM_FIXTURE, vectors), start=1)
        ]

    def list_chunks(self, document_id: str) -> list[dict]:
        return self.chunks if document_id == "term-fixture" else []


def load_cases(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    cases = load_cases(ROOT / "eval" / "term_search_regression.jsonl")
    repository = FixtureChunkRepository()
    retrieval = RetrievalService(repository, EmbeddingService(repository.embedding_provider))
    planner = QueryPlanner()

    results = []
    for case in cases:
        chunks = repository.list_chunks("term-fixture")
        plan = planner.plan_for_retrieval(case["query"], chunks)
        search_results = retrieval.search("term-fixture", case["query"], top_k=4)
        pages = [int(result.chunk["page_number"]) for result in search_results]
        expected_pages = case["expected_pages"]
        selected = plan.selected_spelling_candidate
        passed = pages[: len(expected_pages)] == expected_pages and selected == case["expected_selected_spelling_candidate"]
        results.append(
            {
                "case_id": case["case_id"],
                "query": case["query"],
                "expected_pages": expected_pages,
                "actual_pages": pages,
                "expected_selected_spelling_candidate": case["expected_selected_spelling_candidate"],
                "actual_selected_spelling_candidate": selected,
                "query_plan": plan.debug(),
                "top_results": [
                    {
                        "chunk_id": result.chunk["chunk_id"],
                        "page_number": result.chunk["page_number"],
                        "heading": result.chunk.get("heading"),
                        "score": result.score,
                        "debug": result.debug,
                    }
                    for result in search_results
                ],
                "passed": passed,
            }
        )

    report = {
        "cases": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": [item["case_id"] for item in results if not item["passed"]],
        "results": results,
    }
    output = ROOT / "eval" / "results" / "term_search_latest.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("cases", "passed", "failed")}, ensure_ascii=False, indent=2))
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
