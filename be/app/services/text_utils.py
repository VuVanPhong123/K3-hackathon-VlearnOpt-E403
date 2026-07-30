from __future__ import annotations

import re
import unicodedata


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.lower()
    value = re.sub(r"\s+", " ", value).strip()
    return value


def strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return stripped.replace("đ", "d").replace("Đ", "D")


def search_normalize(value: str) -> str:
    return strip_accents(normalize_text(value))


def tokenize(value: str) -> list[str]:
    return re.findall(r"[\w]+", search_normalize(value), flags=re.UNICODE)


def estimate_tokens(value: str) -> int:
    return max(1, int(len(re.findall(r"\S+", value or "")) * 1.25))


def snippet(text: str, max_chars: int = 360) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def contains_prompt_injection(value: str) -> bool:
    normalized = search_normalize(value)
    patterns = [
        "ignore previous",
        "bo qua huong dan",
        "quyen admin",
        "system prompt",
        "developer message",
        "api key",
        "lam theo lenh moi",
    ]
    return any(pattern in normalized for pattern in patterns)
