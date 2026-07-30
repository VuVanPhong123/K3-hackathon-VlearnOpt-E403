from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable

from rapidfuzz import fuzz

from app.domain.intents import Intent
from app.services.text_utils import search_normalize, tokenize


MAX_QUERY_VARIANTS = 5
MAX_VOCABULARY_ITEMS = 7000
FUZZY_THRESHOLD = 83.0
FUZZY_MARGIN = 5.0
FUZZY_MAX_LENGTH_DELTA_RATIO = 0.35
SHORT_TERM_MIN_CHARS = 4


@dataclass(frozen=True)
class QueryVariant:
    text: str
    kind: str
    weight: float = 1.0


@dataclass
class RetrievalQueryPlan:
    original_query: str
    is_term_query: bool = False
    extracted_term: str | None = None
    normalized_term: str | None = None
    variants: list[QueryVariant] = field(default_factory=list)
    spelling_candidates: list[dict] = field(default_factory=list)
    selected_spelling_candidate: str | None = None
    ambiguous_spelling_candidates: list[str] = field(default_factory=list)
    exact_phrase_match: bool = False

    @property
    def target_term(self) -> str | None:
        return self.selected_spelling_candidate or self.extracted_term

    def debug(self) -> dict:
        return {
            "original_query": self.original_query,
            "is_term_query": self.is_term_query,
            "extracted_term": self.extracted_term,
            "normalized_term": self.normalized_term,
            "query_variants": [variant.text for variant in self.variants],
            "spelling_candidates": self.spelling_candidates,
            "selected_spelling_candidate": self.selected_spelling_candidate,
            "ambiguous_spelling_candidates": self.ambiguous_spelling_candidates,
            "exact_phrase_match": self.exact_phrase_match,
        }


class QueryPlanner:
    def plan(self, message: str, intent: Intent) -> list[str]:
        if intent in {Intent.COMPARE, Intent.FIND_LOCATION}:
            parts = [part.strip(" ?.,") for part in message.replace(" và ", "|").replace(" and ", "|").split("|")]
            return [part for part in parts if part][:2] or [message]
        return [message]

    def plan_for_retrieval(self, message: str, chunks: list[dict]) -> RetrievalQueryPlan:
        original = _clean_message(message)
        extracted = extract_term_query(original)
        if not extracted:
            return RetrievalQueryPlan(
                original_query=message,
                variants=[QueryVariant(original or message, "original", 1.0)],
            )

        normalized_term = normalize_phrase(extracted)
        exact_match = document_has_phrase(chunks, extracted)
        selected, candidates, ambiguous = self._spelling_correction(extracted, chunks, exact_match=exact_match)

        variants = self._variants(original, extracted, selected)
        return RetrievalQueryPlan(
            original_query=message,
            is_term_query=True,
            extracted_term=extracted,
            normalized_term=normalized_term,
            variants=variants,
            spelling_candidates=candidates,
            selected_spelling_candidate=selected,
            ambiguous_spelling_candidates=ambiguous,
            exact_phrase_match=exact_match,
        )

    def _variants(
        self,
        original_query: str,
        extracted_term: str,
        selected_spelling_candidate: str | None,
    ) -> list[QueryVariant]:
        variants: list[QueryVariant] = [QueryVariant(original_query, "original", 0.92)]
        self._append_variant(variants, extracted_term, "extracted_term", 1.12)
        normalized = normalize_phrase(extracted_term)
        self._append_variant(variants, normalized, "normalized_term", 1.08)
        stripped = normalize_phrase(search_normalize(extracted_term))
        self._append_variant(variants, stripped, "accent_stripped_term", 1.0)

        hyphen_variant = hyphen_alternate(extracted_term)
        if hyphen_variant:
            self._append_variant(variants, hyphen_variant, "hyphen_variant", 1.02)

        if selected_spelling_candidate:
            self._append_variant(variants, selected_spelling_candidate, "spelling_candidate", 0.9)

        return variants[:MAX_QUERY_VARIANTS]

    @staticmethod
    def _append_variant(variants: list[QueryVariant], text: str, kind: str, weight: float) -> None:
        clean = _strip_term(text)
        if not clean:
            return
        normalized = clean.casefold()
        if any(item.text.casefold() == normalized for item in variants):
            return
        variants.append(QueryVariant(clean, kind, weight))

    def _spelling_correction(
        self,
        term: str,
        chunks: list[dict],
        *,
        exact_match: bool,
    ) -> tuple[str | None, list[dict], list[str]]:
        term_norm = normalize_phrase(term)
        term_tokens = tokenize(term)
        if exact_match or len(term_norm) < SHORT_TERM_MIN_CHARS or not term_tokens:
            return None, [], []

        vocabulary = build_document_vocabulary(chunks, ngram_size=len(term_tokens))
        scored: list[tuple[str, float]] = []
        for candidate in vocabulary:
            candidate_norm = normalize_phrase(candidate)
            if not _fuzzy_candidate_allowed(term_norm, candidate_norm):
                continue
            score = float(fuzz.ratio(term_norm, candidate_norm))
            if score >= FUZZY_THRESHOLD:
                scored.append((candidate, score))

        scored.sort(key=lambda item: (-item[1], item[0]))
        top = scored[:3]
        candidates = [{"term": term, "candidate": candidate, "score": round(score, 2)} for candidate, score in top]
        if not top:
            return None, [], []

        if len(top) > 1 and top[0][1] - top[1][1] < FUZZY_MARGIN:
            return None, candidates, [candidate for candidate, _ in top]
        return top[0][0], candidates, []


def extract_term_query(message: str) -> str | None:
    clean = _strip_terminal_fillers(_clean_message(message))
    if not clean:
        return None
    searchable = search_normalize(clean)

    patterns = [
        r"^(?:please\s+)?(?:can you\s+)?what is (?P<term>.+?)(?: used for)?$",
        r"^what does (?P<term>.+?) mean$",
        r"^(?:please\s+)?define (?P<term>.+)$",
        r"^(?:please\s+)?explain (?P<term>.+)$",
        r"^tell me about (?P<term>.+)$",
        r"^how does (?P<term>.+?) work$",
        r"^giai thich(?: giup toi| ho toi)? (?P<term>.+)$",
        r"^khai niem (?P<term>.+)$",
        r"^cho toi biet ve (?P<term>.+)$",
        r"^(?P<term>.+?) (?:co nghia la gi|nghia la gi|la gi)(?: the)?$",
        r"^(?P<term>.+?) hoat dong (?:nhu the nao|the nao)$",
        r"^(?P<term>.+?) dung de lam gi$",
    ]
    for pattern in patterns:
        match = re.match(pattern, searchable, flags=re.IGNORECASE)
        if not match:
            continue
        term = clean[match.start("term") : match.end("term")]
        term = _strip_term(term)
        if _looks_like_term(term):
            return term
    return None


def document_has_phrase(chunks: list[dict], phrase: str) -> bool:
    needle = f" {normalize_phrase(phrase)} "
    if needle.strip() == "":
        return False
    return any(needle in f" {chunk_search_text(chunk)} " for chunk in chunks)


def chunk_search_text(chunk: dict) -> str:
    return normalize_phrase(" ".join(str(chunk.get(field) or "") for field in ("heading", "text")))


def normalize_phrase(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").casefold()
    normalized = search_normalize(normalized)
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    return re.sub(r"\s+", " ", normalized).strip()


def hyphen_alternate(value: str) -> str | None:
    clean = _strip_term(value)
    if "-" in clean:
        return re.sub(r"\s+", " ", clean.replace("-", " ")).strip()
    tokens = clean.split()
    if 2 <= len(tokens) <= 4 and all(re.fullmatch(r"[A-Za-z0-9]+", token) for token in tokens):
        return " ".join(["-".join(tokens[:2]), *tokens[2:]])
    return None


def build_document_vocabulary(chunks: list[dict], *, ngram_size: int) -> list[str]:
    wanted_sizes = {max(1, ngram_size)}
    if ngram_size > 1:
        wanted_sizes.add(ngram_size + 1)
        wanted_sizes.add(max(1, ngram_size - 1))
    candidates: dict[str, str] = {}
    for chunk in chunks:
        for field in ("heading", "text"):
            for phrase in _candidate_phrases(str(chunk.get(field) or ""), wanted_sizes):
                normalized = normalize_phrase(phrase)
                if normalized and normalized not in candidates:
                    candidates[normalized] = phrase
                if len(candidates) >= MAX_VOCABULARY_ITEMS:
                    return list(candidates.values())
    return list(candidates.values())


def _candidate_phrases(text: str, wanted_sizes: Iterable[int]) -> list[str]:
    normalized_text = unicodedata.normalize("NFKC", text).replace("-", " ")
    tokens = re.findall(r"[\w]+", normalized_text, flags=re.UNICODE)
    phrases: list[str] = []
    for size in wanted_sizes:
        if size <= 0 or size > 5:
            continue
        for index in range(0, max(0, len(tokens) - size + 1)):
            phrase = " ".join(tokens[index : index + size])
            if _looks_like_term(phrase):
                phrases.append(phrase)
    return phrases


def _clean_message(message: str) -> str:
    normalized = unicodedata.normalize("NFKC", message or "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized.strip(" \t\r\n\"'“”‘’.,!?;:()[]{}")


def _strip_terminal_fillers(value: str) -> str:
    clean = value
    fillers = [
        "nhỉ",
        "nhi",
        "nhé",
        "nhe",
        "nha",
        "vậy",
        "vay",
        "thế",
        "the",
        "được không",
        "duoc khong",
        "please",
    ]
    changed = True
    while changed:
        changed = False
        searchable = search_normalize(clean)
        for filler in fillers:
            normalized_filler = search_normalize(filler)
            suffix = f" {normalized_filler}"
            if searchable.endswith(suffix):
                clean = clean[: -len(suffix)].strip(" \t\r\n\"'“”‘’.,!?;:()[]{}")
                changed = True
                break
    return clean


def _strip_term(value: str) -> str:
    clean = _clean_message(value)
    clean = re.sub(
        r"^(?:giúp tôi|giup toi|hộ tôi|ho toi|please|can you)\s+",
        "",
        clean,
        flags=re.IGNORECASE,
    )
    return _clean_message(clean)


def _looks_like_term(term: str) -> bool:
    normalized = normalize_phrase(term)
    tokens = normalized.split()
    if not tokens:
        return False
    if normalized in {"hinh nay", "so do nay", "bieu do nay", "bang nay", "trang nay"}:
        return False
    if " va " in f" {normalized} " or " and " in f" {normalized} ":
        return False
    if len(normalized) < 2 or len(tokens) > 8:
        return False
    return any(len(token) >= 2 for token in tokens)


def _fuzzy_candidate_allowed(term_norm: str, candidate_norm: str) -> bool:
    if term_norm == candidate_norm:
        return False
    if term_norm.startswith(candidate_norm) or candidate_norm.startswith(term_norm):
        return False
    if len(term_norm) < SHORT_TERM_MIN_CHARS or len(candidate_norm) < SHORT_TERM_MIN_CHARS:
        return False
    longer = max(len(term_norm), len(candidate_norm))
    if abs(len(term_norm) - len(candidate_norm)) / longer > FUZZY_MAX_LENGTH_DELTA_RATIO:
        return False
    term_tokens = term_norm.split()
    candidate_tokens = candidate_norm.split()
    if len(term_tokens) != len(candidate_tokens):
        return False
    if term_norm[0] != candidate_norm[0]:
        return False
    if len(term_tokens) > 1:
        term_initials = "".join(token[0] for token in term_tokens if token)
        candidate_initials = "".join(token[0] for token in candidate_tokens if token)
        if term_initials != candidate_initials:
            return False
    return True
