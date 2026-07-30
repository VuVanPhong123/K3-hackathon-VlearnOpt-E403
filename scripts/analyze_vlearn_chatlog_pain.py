#!/usr/bin/env python3
"""Mine VLearn chatlog for CP1 selected-context/retrieval pain evidence.

The script intentionally uses only Python standard library so the counting
rules are easy to rerun in a fresh repo checkout.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_CSV = Path("data/vlearn-pack/chatlog/chat_history_anonymized_for_hackathon.csv")

# Count retrieval/fallback language after accent stripping. These patterns were
# fixed before selecting evidence examples and are not tuned to make counts nicer.
RETRIEVAL_FAILURE_PATTERNS = [
    r"khong tim thay",
    r"chua tim thay",
    r"khong chua thong tin",
    r"khong co tai lieu",
    r"cung cap them thong tin",
    r"cung cap noi dung hoac tieu de",
    r"cung cap noi dung",
    r"cung cap.*tieu de",
]

WHOLE_SUMMARY_PATTERNS = [
    r"tom tat.*toan bo",
    r"tong hop.*toan bo",
    r"tom tat.*buoi hoc",
    r"tom tat.*ngay hom nay",
    r"tom tat.*hom nay",
    r"tom gon.*day",
    r"toan bo slide",
    r"toan bo tai lieu",
    r"toan bo bai giang",
    r"tai lieu toi xem",
]

VISUAL_CONTEXT_PATTERNS = [
    r"bieu do",
    r"do thi",
    r"hinh anh",
    r"\bhinh\b",
    r"boi do",
    r"visual",
    r"chart",
]


def normalize(text: str | None) -> str:
    """Lowercase and remove Vietnamese accents for robust regex matching."""
    text = (text or "").lower()
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def compile_any(patterns: list[str]) -> re.Pattern[str]:
    return re.compile("|".join(patterns), re.IGNORECASE)


RETRIEVAL_FAILURE_RE = compile_any(RETRIEVAL_FAILURE_PATTERNS)
WHOLE_SUMMARY_RE = compile_any(WHOLE_SUMMARY_PATTERNS)
VISUAL_CONTEXT_RE = compile_any(VISUAL_CONTEXT_PATTERNS)
PAGE_RE = re.compile(r"Trang\s*(\d+)", re.IGNORECASE)


def read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_citations(raw: str | None) -> list[int]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    citations: list[int] = []
    for item in parsed:
        try:
            citations.append(int(item))
        except (TypeError, ValueError):
            continue
    return citations


def citations_empty(row: dict[str, str]) -> bool:
    return (row.get("citations") or "").strip() in {"", "[]"}


def selected_page(student_content: str) -> int | None:
    match = PAGE_RE.search(student_content or "")
    return int(match.group(1)) if match else None


def is_retrieval_failure(tutor_content: str) -> bool:
    return bool(RETRIEVAL_FAILURE_RE.search(normalize(tutor_content)))


def has_whole_summary_intent(student_content: str) -> bool:
    return bool(WHOLE_SUMMARY_RE.search(normalize(student_content)))


def has_visual_context_intent(student_content: str) -> bool:
    return bool(VISUAL_CONTEXT_RE.search(normalize(student_content)))


def build_turns(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    turns: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        turns[row["turn_id"]][row["role"]] = row
    return dict(turns)


def pct(count: int, total: int) -> str:
    if total == 0:
        return "0.0%"
    return f"{count / total * 100:.1f}%"


def compact(text: str, limit: int = 130) -> str:
    one_line = " ".join((text or "").split())
    return one_line if len(one_line) <= limit else one_line[: limit - 3] + "..."


def turn_record(turn_id: str, pair: dict[str, dict[str, str]]) -> dict[str, Any]:
    student = pair.get("student", {})
    tutor = pair.get("tutor", {})
    page = selected_page(student.get("content", ""))
    citations = parse_citations(tutor.get("citations", ""))
    mismatch = bool(page is not None and citations and page not in citations)
    retrieval_failure = is_retrieval_failure(tutor.get("content", ""))
    return {
        "conversation_id": student.get("conversation_id") or tutor.get("conversation_id"),
        "turn_id": turn_id,
        "day_code": student.get("day_code") or tutor.get("day_code"),
        "student_message_id": student.get("message_id"),
        "tutor_message_id": tutor.get("message_id"),
        "selected_page": page,
        "citations": tutor.get("citations", ""),
        "rating": tutor.get("rating", ""),
        "retrieval_failure": retrieval_failure,
        "empty_citations": citations_empty(tutor),
        "page_citation_mismatch": mismatch,
        "whole_summary_intent": has_whole_summary_intent(student.get("content", "")),
        "visual_context_intent": has_visual_context_intent(student.get("content", "")),
        "student_quote": student.get("content", ""),
        "tutor_quote": tutor.get("content", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()

    rows = read_rows(args.csv)
    turns = build_turns(rows)
    tutor_rows = [row for row in rows if row["role"] == "tutor"]
    student_rows = [row for row in rows if row["role"] == "student"]
    records = [
        turn_record(turn_id, pair)
        for turn_id, pair in turns.items()
        if "student" in pair and "tutor" in pair
    ]

    tutor_response_count = len(tutor_rows)
    empty_citation_count = sum(citations_empty(row) for row in tutor_rows)
    retrieval_failure_count = sum(is_retrieval_failure(row["content"]) for row in tutor_rows)
    retrieval_failure_down = sum(
        is_retrieval_failure(row["content"]) and row.get("rating") == "down"
        for row in tutor_rows
    )
    rated_tutor_count = sum(bool(row.get("rating")) for row in tutor_rows)
    rated_up = sum(row.get("rating") == "up" for row in tutor_rows)
    rated_down = sum(row.get("rating") == "down" for row in tutor_rows)

    page_records = [record for record in records if record["selected_page"] is not None]
    page_retrieval_failures = [
        record for record in page_records if record["retrieval_failure"]
    ]
    strong_page_retrieval_failures = [
        record
        for record in page_records
        if record["retrieval_failure"] and record["empty_citations"]
    ]
    page_mismatches = [
        record for record in page_records if record["page_citation_mismatch"]
    ]
    whole_summary_records = [
        record for record in records if record["whole_summary_intent"]
    ]
    whole_summary_failures = [
        record
        for record in whole_summary_records
        if record["retrieval_failure"] or record["empty_citations"]
    ]
    visual_records = [record for record in records if record["visual_context_intent"]]
    visual_failures = [
        record
        for record in visual_records
        if record["retrieval_failure"] or record["page_citation_mismatch"]
    ]

    print("Aggregate results")
    print(f"- Total messages: {len(rows)}")
    print(f"- Total question-answer turns: {len(turns)}")
    print(f"- Total tutor responses: {tutor_response_count}")
    print(
        f"- Tutor responses with empty citations: {empty_citation_count}/"
        f"{tutor_response_count} ({pct(empty_citation_count, tutor_response_count)})"
    )
    print(
        f"- Tutor responses with retrieval/fallback language: "
        f"{retrieval_failure_count}/{tutor_response_count} "
        f"({pct(retrieval_failure_count, tutor_response_count)})"
    )
    print(f"- Retrieval/fallback responses with rating=down: {retrieval_failure_down}")
    print(
        f"- Rated tutor responses: {rated_tutor_count} "
        f"(up={rated_up}, down={rated_down})"
    )
    print(f"- Student turns mentioning Trang N: {len(page_records)}")
    print(
        f"- Trang N + retrieval/fallback language: {len(page_retrieval_failures)}"
    )
    print(
        f"- Trang N + retrieval/fallback language + empty citations: "
        f"{len(strong_page_retrieval_failures)}"
    )
    print(f"- Trang N + citation does not include selected page: {len(page_mismatches)}")
    print(
        f"- Whole-session/document summary intents: {len(whole_summary_records)}; "
        f"with failure/empty citation signal: {len(whole_summary_failures)}"
    )
    print(
        f"- Visual/chart/image intents: {len(visual_records)}; "
        f"with failure/mismatch signal: {len(visual_failures)}"
    )

    print("\nCandidate turns")
    candidates = [
        record
        for record in records
        if record["selected_page"] is not None
        and (
            record["retrieval_failure"]
            or record["page_citation_mismatch"]
            or (record["empty_citations"] and record["rating"] == "down")
        )
    ]
    candidates.sort(
        key=lambda record: (
            record["rating"] != "down",
            not record["retrieval_failure"],
            not record["page_citation_mismatch"],
            record["conversation_id"],
            record["turn_id"],
        )
    )
    for index, record in enumerate(candidates[: args.limit], start=1):
        print(
            f"{index:02d}. {record['conversation_id']}/{record['turn_id']} "
            f"page={record['selected_page']} citations={record['citations']} "
            f"rating={record['rating'] or 'null'} "
            f"rf={record['retrieval_failure']} mismatch={record['page_citation_mismatch']}"
        )
        print(f"    student: {compact(record['student_quote'])}")
        print(f"    tutor:   {compact(record['tutor_quote'])}")


if __name__ == "__main__":
    main()
