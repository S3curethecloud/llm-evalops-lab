from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    id: str
    text: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class SearchResult:
    document: Document
    score: float


class TokenIndex:
    """Tiny cosine-similarity retrieval index using only the standard library."""

    def __init__(self, documents: list[Document]) -> None:
        self.documents = documents
        self._vectors = [_vectorize(doc.text) for doc in documents]

    @classmethod
    def from_paths(cls, paths: list[str | Path]) -> TokenIndex:
        documents: list[Document] = []
        for path in paths:
            current = Path(path)
            documents.append(
                Document(
                    id=str(current),
                    text=current.read_text(encoding="utf-8"),
                    metadata={"path": str(current)},
                )
            )
        return cls(documents)

    def search(self, query: str, *, top_k: int = 3) -> list[SearchResult]:
        query_vector = _vectorize(query)
        ranked = [
            SearchResult(document=doc, score=_cosine(query_vector, vector))
            for doc, vector in zip(self.documents, self._vectors, strict=True)
        ]
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:top_k]


def _vectorize(text: str) -> Counter[str]:
    return Counter(re.findall(r"[a-z0-9]+", text.lower()))


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in intersection)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
