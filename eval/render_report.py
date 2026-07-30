from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import subprocess
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DIMENSIONS = {
    "status": "HTTP status khớp expected.",
    "mode": "Chế độ tương tác khớp expected.",
    "page_context": "Trang dùng đúng tập trang bắt buộc và không dùng trang cấm.",
    "citation": "Citation có/không và số trang khớp expected.",
    "provider_invocation": "Có hoặc không gọi provider đúng như expected.",
    "media_path": "Đường gọi text/multimodal và việc đính ảnh khớp expected.",
    "fallback": "Provider, fallback và thứ tự provider khớp expected.",
    "prompt_context": "Prompt chứa đủ chuỗi bắt buộc và không chứa chuỗi cấm.",
    "history_limit": "Số message lịch sử không vượt giới hạn expected.",
    "utf8_response": "Output tiếng Việt giữ được ký tự có dấu.",
    "error_detail": "Thông báo lỗi chứa đủ nội dung bắt buộc.",
    "decision": "Decision answer/clarify/abstain khớp expected.",
    "clarification": "Cờ needs_clarification khớp expected.",
    "abstention": "Cờ abstained khớp expected.",
    "no_crash": "Case kết thúc có kiểm soát, không phát sinh exception ngoài contract.",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_metadata() -> tuple[str, bool]:
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    dirty = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=ROOT,
            text=True,
        ).strip()
    )
    return sha, dirty


def load_coverage(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            row["case_id"]: row
            for row in csv.DictReader(handle)
        }


def fmt_percent(value: object) -> str:
    if isinstance(value, float):
        return f"{value * 100:.1f}%"
    return str(value)


def render(report: dict, coverage: dict[str, dict[str, str]], input_path: Path) -> str:
    git_sha, dirty = git_metadata()
    golden_path = ROOT / "eval" / "golden_set.jsonl"
    lines = [
        "# VLearn Tutor — Offline Evaluation Report",
        "",
        "## Run metadata",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Generated | {datetime.now().astimezone().isoformat(timespec='seconds')} |",
        f"| Git SHA | `{git_sha}` |",
        f"| Working tree | {'dirty (kết quả trước commit)' if dirty else 'clean'} |",
        f"| Python | `{platform.python_version()}` |",
        f"| Platform | `{platform.platform()}` |",
        f"| Golden set | `{golden_path.relative_to(ROOT)}` |",
        f"| Golden SHA-256 | `{sha256(golden_path)}` |",
        f"| Raw report | `{input_path.relative_to(ROOT)}` |",
        "| Execution mode | Offline, deterministic `RecordingProvider` |",
        "| Retrieval in eval | Fixture chunks + hash embedding |",
        "",
        "## Quality dimensions",
        "",
        "| Dimension | Reproducible pass condition |",
        "|---|---|",
    ]
    lines.extend(
        f"| `{name}` | {description} |"
        for name, description in DIMENSIONS.items()
    )
    lines.extend(
        [
            "",
            "## Quality bar result",
            "",
            "| Metric | Actual | Threshold | Result |",
            "|---|---:|---:|:---:|",
        ]
    )
    for metric, threshold in report["quality_bar"].items():
        actual = report["metrics"].get(metric, 0.0)
        lines.append(
            f"| `{metric}` | {fmt_percent(actual)} | "
            f"{fmt_percent(threshold)} | {'PASS' if actual >= threshold else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            f"**Overall quality bar:** {'PASS' if report['quality_bar_passed'] else 'FAIL'}",
            "",
            "## Complete case table",
            "",
            "| Case | Source | Layer | Tier | Applicable checks | Result | Failed dimensions |",
            "|---|---|:---:|---|---|:---:|---|",
        ]
    )
    for item in report["results"]:
        case = item["case"]
        case_id = item["case_id"]
        mapping = coverage.get(case_id, {})
        applicable = [
            key
            for key, value in item["scores"].items()
            if key != "passed" and value is not None
        ]
        failed = [
            key
            for key, value in item["scores"].items()
            if key != "passed" and value is False
        ]
        source = case.get("source", {}).get("type", "unknown")
        lines.append(
            f"| `{case_id}` | `{source}` | {mapping.get('risk_layer', '—')} | "
            f"{mapping.get('difficulty', '—')} | {', '.join(applicable)} | "
            f"{'PASS' if item['scores']['passed'] else 'FAIL'} | "
            f"{', '.join(failed) if failed else '—'} |"
        )
    lines.extend(
        [
            "",
            "## Failed cases",
            "",
        ]
    )
    if report["failed_cases"]:
        lines.extend(f"- `{case_id}`" for case_id in report["failed_cases"])
    else:
        lines.append("- Không có.")
    lines.extend(
        [
            "",
            "## Scope and limitations",
            "",
            "- Report này đo routing, context priority, citation contract, provider/fallback path, "
            "conditional decision và khả năng không crash.",
            "- `RecordingProvider` trả output định sẵn; report này không chứng minh chất lượng ngôn ngữ "
            "hoặc semantic groundedness của model thật.",
            "- API thật và multimodal thật được chứng minh riêng trong "
            "`evidence/r5-live-ai-run.md`.",
            "- Không có API key, header, PDF/base64 hoặc raw chatlog trong report.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "eval" / "results" / "latest.json",
    )
    parser.add_argument(
        "--coverage",
        type=Path,
        default=ROOT / "eval" / "coverage-map.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "eval" / "results" / "latest.md",
    )
    args = parser.parse_args()

    report = json.loads(args.input.read_text(encoding="utf-8"))
    coverage = load_coverage(args.coverage)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render(report, coverage, args.input),
        encoding="utf-8",
    )
    print(args.output)


if __name__ == "__main__":
    main()
