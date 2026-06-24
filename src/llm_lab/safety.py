from __future__ import annotations

import re
from dataclasses import dataclass, field

_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
]

_PII_PATTERNS = [
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
]


@dataclass(frozen=True)
class SafetyFinding:
    category: str
    message: str


@dataclass(frozen=True)
class SafetyPolicy:
    blocked_phrases: list[str] = field(default_factory=lambda: ["ignore previous instructions"])

    def inspect(self, text: str) -> list[SafetyFinding]:
        findings: list[SafetyFinding] = []
        lowered = text.lower()

        for phrase in self.blocked_phrases:
            if phrase.lower() in lowered:
                findings.append(SafetyFinding("blocked_phrase", f"Blocked phrase found: {phrase}"))

        if any(pattern.search(text) for pattern in _SECRET_PATTERNS):
            findings.append(SafetyFinding("secret", "Potential secret or API key detected"))

        if any(pattern.search(text) for pattern in _PII_PATTERNS):
            findings.append(SafetyFinding("pii", "Potential sensitive identifier detected"))

        return findings
