from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path


EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_set.jsonl"
COVERAGE_MAP_PATH = EVAL_DIR / "coverage-map.csv"

REQUIRED_COLUMNS = {
    "case_id",
    "source_type",
    "source_ref",
    "risk_layer",
    "difficulty",
    "scenario_id",
}
ALLOWED_LAYERS = {
    "1_truth",
    "2_ambiguity",
    "3_scope_authority",
    "4_domain",
}
ALLOWED_DIFFICULTIES = {"routine", "hard", "rare"}
EXPECTED_ROUTINE_COUNT = 10
EXPECTED_RARE_COUNT = 4
MIN_CASES_PER_LAYER = 2
MIN_CHATLOG_CASES = 10


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _load_golden_set(errors: list[str]) -> dict[str, dict[str, str]]:
    cases: dict[str, dict[str, str]] = {}

    with GOLDEN_SET_PATH.open(encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            try:
                case = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                errors.append(
                    f"{GOLDEN_SET_PATH.name}:{line_number}: JSON không hợp lệ: {exc}"
                )
                continue

            case_id = str(case.get("case_id", "")).strip()
            if not case_id:
                errors.append(
                    f"{GOLDEN_SET_PATH.name}:{line_number}: thiếu case_id"
                )
                continue
            if case_id in cases:
                errors.append(
                    f"{GOLDEN_SET_PATH.name}:{line_number}: case_id trùng {case_id!r}"
                )
                continue

            source = case.get("source")
            if not isinstance(source, dict):
                errors.append(
                    f"{GOLDEN_SET_PATH.name}:{line_number}: source của {case_id!r} "
                    "phải là object"
                )
                continue

            source_type = str(source.get("type", "")).strip()
            source_ref = ""
            if source_type == "vlearn_chatlog_adapted":
                conversation_id = str(source.get("conversation_id", "")).strip()
                turn_id = str(source.get("turn_id", "")).strip()
                if not conversation_id or not turn_id:
                    errors.append(
                        f"{GOLDEN_SET_PATH.name}:{line_number}: {case_id!r} thiếu "
                        "conversation_id/turn_id"
                    )
                source_ref = f"{conversation_id}/{turn_id}"
            elif source_type != "synthetic":
                errors.append(
                    f"{GOLDEN_SET_PATH.name}:{line_number}: source.type không hỗ trợ "
                    f"{source_type!r} cho {case_id!r}"
                )

            cases[case_id] = {
                "source_type": source_type,
                "source_ref": source_ref,
            }

    return cases


def _load_coverage_map(errors: list[str]) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}

    with COVERAGE_MAP_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        extra_columns = columns - REQUIRED_COLUMNS
        if missing_columns:
            errors.append(
                f"{COVERAGE_MAP_PATH.name}: thiếu cột "
                + ", ".join(sorted(missing_columns))
            )
        if extra_columns:
            errors.append(
                f"{COVERAGE_MAP_PATH.name}: cột không mong đợi "
                + ", ".join(sorted(extra_columns))
            )

        for line_number, raw_row in enumerate(reader, start=2):
            row = {
                key: (value or "").strip()
                for key, value in raw_row.items()
                if key is not None
            }
            case_id = row.get("case_id", "")
            if not case_id:
                errors.append(
                    f"{COVERAGE_MAP_PATH.name}:{line_number}: thiếu case_id"
                )
                continue
            if case_id in rows:
                errors.append(
                    f"{COVERAGE_MAP_PATH.name}:{line_number}: case_id trùng "
                    f"{case_id!r}"
                )
                continue

            if row.get("risk_layer") not in ALLOWED_LAYERS:
                errors.append(
                    f"{COVERAGE_MAP_PATH.name}:{line_number}: risk_layer không hợp lệ "
                    f"{row.get('risk_layer')!r}"
                )
            if row.get("difficulty") not in ALLOWED_DIFFICULTIES:
                errors.append(
                    f"{COVERAGE_MAP_PATH.name}:{line_number}: difficulty không hợp lệ "
                    f"{row.get('difficulty')!r}"
                )
            if not row.get("scenario_id"):
                errors.append(
                    f"{COVERAGE_MAP_PATH.name}:{line_number}: thiếu scenario_id"
                )

            rows[case_id] = row

    return rows


def validate() -> int:
    errors: list[str] = []

    if not GOLDEN_SET_PATH.is_file():
        errors.append(f"Không tìm thấy {GOLDEN_SET_PATH}")
    if not COVERAGE_MAP_PATH.is_file():
        errors.append(f"Không tìm thấy {COVERAGE_MAP_PATH}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    golden_cases = _load_golden_set(errors)
    coverage_rows = _load_coverage_map(errors)

    golden_ids = set(golden_cases)
    coverage_ids = set(coverage_rows)
    missing_ids = golden_ids - coverage_ids
    extra_ids = coverage_ids - golden_ids
    if missing_ids:
        errors.append(
            "Coverage map thiếu case: " + ", ".join(sorted(missing_ids))
        )
    if extra_ids:
        errors.append(
            "Coverage map có case không tồn tại trong golden set: "
            + ", ".join(sorted(extra_ids))
        )

    for case_id in sorted(golden_ids & coverage_ids):
        golden_source = golden_cases[case_id]
        coverage_source = coverage_rows[case_id]
        if coverage_source["source_type"] != golden_source["source_type"]:
            errors.append(
                f"{case_id}: source_type={coverage_source['source_type']!r}, "
                f"golden={golden_source['source_type']!r}"
            )
        if coverage_source["source_ref"] != golden_source["source_ref"]:
            errors.append(
                f"{case_id}: source_ref={coverage_source['source_ref']!r}, "
                f"golden={golden_source['source_ref']!r}"
            )

    layer_counts = Counter(
        row["risk_layer"]
        for case_id, row in coverage_rows.items()
        if case_id in golden_ids
    )
    for layer in sorted(ALLOWED_LAYERS):
        if layer_counts[layer] < MIN_CASES_PER_LAYER:
            errors.append(
                f"{layer}: cần ít nhất {MIN_CASES_PER_LAYER} case, "
                f"hiện có {layer_counts[layer]}"
            )

    difficulty_counts = Counter(
        row["difficulty"]
        for case_id, row in coverage_rows.items()
        if case_id in golden_ids
    )
    if difficulty_counts["routine"] != EXPECTED_ROUTINE_COUNT:
        errors.append(
            f"routine: cần đúng {EXPECTED_ROUTINE_COUNT}, "
            f"hiện có {difficulty_counts['routine']}"
        )
    if difficulty_counts["rare"] != EXPECTED_RARE_COUNT:
        errors.append(
            f"rare: cần đúng {EXPECTED_RARE_COUNT}, "
            f"hiện có {difficulty_counts['rare']}"
        )

    source_counts = Counter(
        case["source_type"] for case in golden_cases.values()
    )
    if source_counts["vlearn_chatlog_adapted"] < MIN_CHATLOG_CASES:
        errors.append(
            "vlearn_chatlog_adapted: cần ít nhất "
            f"{MIN_CHATLOG_CASES}, hiện có "
            f"{source_counts['vlearn_chatlog_adapted']}"
        )

    if errors:
        print("Coverage validation FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Coverage validation PASSED")
    print(f"- Golden cases: {len(golden_cases)}")
    print(
        "- Sources: "
        + ", ".join(
            f"{name}={count}" for name, count in sorted(source_counts.items())
        )
    )
    print(
        "- Risk layers: "
        + ", ".join(
            f"{name}={layer_counts[name]}" for name in sorted(ALLOWED_LAYERS)
        )
    )
    print(
        "- Difficulty: "
        + ", ".join(
            f"{name}={difficulty_counts[name]}"
            for name in sorted(ALLOWED_DIFFICULTIES)
        )
    )
    return 0


if __name__ == "__main__":
    _configure_console()
    raise SystemExit(validate())
