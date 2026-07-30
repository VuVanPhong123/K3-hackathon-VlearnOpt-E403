from __future__ import annotations


def _optional_equal(expected: dict, key: str, actual) -> bool | None:
    return actual == expected[key] if key in expected else None


def _pages_match(expected: dict, actual: list[int]) -> bool | None:
    if "exact_pages" in expected:
        return actual == expected["exact_pages"]
    if "must_include_pages" in expected:
        required = expected["must_include_pages"]
        forbidden = expected.get("must_not_include_pages", [])
        return all(page in actual for page in required) and all(
            page not in actual for page in forbidden
        )
    return None


def _citation_match(expected: dict, prediction: dict) -> bool | None:
    actual = prediction.get("citation_pages", [])
    if "exact_citation_pages" in expected:
        return actual == expected["exact_citation_pages"]
    if "citation_required" in expected:
        if not expected["citation_required"]:
            return actual == []
        required = expected.get(
            "must_include_pages",
            expected.get("exact_pages", []),
        )
        return bool(actual) and all(page in actual for page in required)
    return None


def _provider_invocation(expected: dict, prediction: dict) -> bool | None:
    if "provider_called" not in expected:
        return None
    return prediction.get("provider_called") is expected["provider_called"]


def _media_path(expected: dict, prediction: dict) -> bool | None:
    checks = []
    if "call_kind" in expected:
        calls = prediction.get("call_kinds", [])
        checks.append(bool(calls) and calls[-1] == expected["call_kind"])
    if "image_used" in expected:
        checks.append(prediction.get("image_used") is expected["image_used"])
    if expected.get("call_kind") == "multimodal":
        checks.append(prediction.get("all_images_attached") is True)
    return all(checks) if checks else None


def _fallback(expected: dict, prediction: dict) -> bool | None:
    checks = []
    if "provider" in expected:
        checks.append(prediction.get("provider") == expected["provider"])
    if "fallback_used" in expected:
        checks.append(
            prediction.get("fallback_used") is expected["fallback_used"]
        )
    if "attempted_providers" in expected:
        checks.append(
            prediction.get("attempted_providers")
            == expected["attempted_providers"]
        )
    return all(checks) if checks else None


def _prompt_context(expected: dict, prediction: dict) -> bool | None:
    required = expected.get("prompt_must_contain")
    forbidden = expected.get("prompt_must_not_contain")
    if required is None and forbidden is None:
        return None
    payload = "\n".join(prediction.get("provider_inputs", []))
    return all(value in payload for value in required or []) and all(
        value not in payload for value in forbidden or []
    )


def _history_limit(expected: dict, prediction: dict) -> bool | None:
    if "max_history_count" not in expected:
        return None
    return prediction.get("max_history_count", 0) <= expected["max_history_count"]


def _utf8_response(expected: dict, prediction: dict) -> bool | None:
    if not expected.get("utf8_required"):
        return None
    return prediction.get("answer_has_vietnamese_diacritics") is True


def _error_detail(expected: dict, prediction: dict) -> bool | None:
    required = expected.get("error_must_contain")
    if not required:
        return None
    return all(value in prediction.get("error", "") for value in required)


def score_case(case: dict, prediction: dict) -> dict:
    expected = case["expected"]
    scores = {
        "status": _optional_equal(
            expected,
            "status_code",
            prediction.get("status_code"),
        ),
        "mode": _optional_equal(expected, "mode", prediction.get("mode")),
        "page_context": _pages_match(
            expected,
            prediction.get("pages_used", []),
        ),
        "citation": _citation_match(expected, prediction),
        "provider_invocation": _provider_invocation(expected, prediction),
        "media_path": _media_path(expected, prediction),
        "fallback": _fallback(expected, prediction),
        "prompt_context": _prompt_context(expected, prediction),
        "history_limit": _history_limit(expected, prediction),
        "utf8_response": _utf8_response(expected, prediction),
        "error_detail": _error_detail(expected, prediction),
        "no_crash": prediction.get("no_crash") is True,
    }
    scores["passed"] = all(value is not False for value in scores.values())
    return scores
