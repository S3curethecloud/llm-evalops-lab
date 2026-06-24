from __future__ import annotations

import re
from collections import Counter

_REFUSAL_PATTERNS = (
    "i can't help",
    "i cannot help",
    "i'm unable",
    "i am unable",
    "as an ai",
)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def exact_match(output: str, ideal: str) -> bool:
    return normalize_text(output) == normalize_text(ideal)


def contains_all(output: str, required: list[str]) -> bool:
    normalized = normalize_text(output)
    return all(normalize_text(item) in normalized for item in required)


def token_f1(output: str, ideal: str) -> float:
    output_tokens = _tokens(output)
    ideal_tokens = _tokens(ideal)
    if not output_tokens and not ideal_tokens:
        return 1.0
    if not output_tokens or not ideal_tokens:
        return 0.0

    overlap = Counter(output_tokens) & Counter(ideal_tokens)
    common = sum(overlap.values())
    if common == 0:
        return 0.0
    precision = common / len(output_tokens)
    recall = common / len(ideal_tokens)
    return 2 * precision * recall / (precision + recall)


def refusal_detected(output: str) -> bool:
    normalized = normalize_text(output)
    return any(pattern in normalized for pattern in _REFUSAL_PATTERNS)


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", normalize_text(value))
