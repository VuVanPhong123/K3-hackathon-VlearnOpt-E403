from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BE = ROOT / "codebase" / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BE))

from app.services.embedding_service import EmbeddingService
from app.services.query_planner import QueryPlanner, normalize_phrase
from app.services.retrieval_service import RetrievalService
from eval.pdf_eval_fixture import DEFAULT_DOCUMENT_ID, PdfEvalFixture


def load_cases(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run term-search regression against a real PDF.")
    parser.add_argument(
        "--document",
        type=Path,
        default=None,
        help="Path to d2-slide-hackathon.pdf. Defaults to eval/fixtures/d2-slide-hackathon.pdf if present.",
    )
    return parser.parse_args()


def _resolve_document_path(path: Path | None) -> Path:
    default = ROOT / "eval" / "fixtures" / "d2-slide-hackathon.pdf"
    document = path or default
    if not document.exists():
        raise FileNotFoundError(
            "Không tìm thấy PDF eval. Truyền rõ --document \"path/to/d2-slide-hackathon.pdf\"; "
            "runner không còn fallback sang fixture thuật ngữ giả."
        )
    return document


def _top_page_ok(case: dict[str, Any], pages: list[int]) -> bool:
    if case.get("expect_no_results"):
        return not pages
    if "expected_top_page" in case:
        return bool(pages) and pages[0] == case["expected_top_page"]
    if "expected_top_page_any_of" in case:
        return bool(pages) and pages[0] in set(case["expected_top_page_any_of"])
    return True


def _include_pages_ok(case: dict[str, Any], pages: list[int]) -> bool:
    if "must_include_pages" in case:
        return all(page in pages for page in case["must_include_pages"])
    if "must_include_any_page" in case:
        return any(page in pages for page in case["must_include_any_page"])
    return True


def _forbidden_pages_ok(case: dict[str, Any], pages: list[int]) -> bool:
    forbidden = set(case.get("must_not_include_pages") or [])
    return all(page not in forbidden for page in pages)


def _candidate_ok(case: dict[str, Any], selected: str | None) -> bool:
    if case.get("expect_no_spelling_candidate"):
        return selected is None
    expected = case.get("expected_selected_spelling_candidate_normalized")
    if expected is None:
        return True
    return selected is not None and normalize_phrase(selected) == expected


def _case_passed(case: dict[str, Any], pages: list[int], selected: str | None) -> bool:
    return all(
        [
            _top_page_ok(case, pages),
            _include_pages_ok(case, pages),
            _forbidden_pages_ok(case, pages),
            _candidate_ok(case, selected),
        ]
    )


def main() -> int:
    args = _parse_args()
    cases = load_cases(ROOT / "eval" / "term_search_regression.jsonl")
    if len(cases) != 14:
        raise RuntimeError(f"Term regression phải có đúng 14 case, hiện có {len(cases)}.")

    with tempfile.TemporaryDirectory(prefix="vlearn-term-eval-") as directory:
        fixture = PdfEvalFixture.from_pdf(
            _resolve_document_path(args.document),
            Path(directory),
            document_id=DEFAULT_DOCUMENT_ID,
        )
        retrieval = RetrievalService(fixture.chunk_repository, EmbeddingService(fixture.embedding_provider))
        planner = QueryPlanner()

        results = []
        chunks = fixture.chunk_repository.list_chunks(DEFAULT_DOCUMENT_ID)
        for case in cases:
            plan = planner.plan_for_retrieval(case["query"], chunks)
            search_results = retrieval.search(DEFAULT_DOCUMENT_ID, case["query"], top_k=4)
            pages = [int(result.chunk["page_number"]) for result in search_results]
            selected = plan.selected_spelling_candidate
            passed = _case_passed(case, pages, selected)
            results.append(
                {
                    "case_id": case["case_id"],
                    "query": case["query"],
                    "expectation": {key: value for key, value in case.items() if key not in {"case_id", "query"}},
                    "actual_pages": pages,
                    "actual_selected_spelling_candidate": selected,
                    "actual_selected_spelling_candidate_normalized": normalize_phrase(selected or "") or None,
                    "query_plan": plan.debug(),
                    "top_results": [
                        {
                            "chunk_id": result.chunk["chunk_id"],
                            "page_number": result.chunk["page_number"],
                            "heading": result.chunk.get("heading"),
                            "score": result.score,
                            "snippet": result.chunk.get("text", "")[:500],
                            "debug": result.debug,
                        }
                        for result in search_results
                    ],
                    "passed": passed,
                }
            )

    report = {
        "document": fixture.manifest,
        "generated_at": datetime.now(UTC).isoformat(),
        "cases": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": [item["case_id"] for item in results if not item["passed"]],
        "results": results,
    }
    output = ROOT / "eval" / "results" / "term_search_latest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "cases": report["cases"],
                "document": fixture.manifest,
                "passed": report["passed"],
                "failed": report["failed"],
                "report": str(output),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
