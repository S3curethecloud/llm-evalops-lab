from __future__ import annotations

import re
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm_lab.providers.base import LLMProvider


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


@dataclass(frozen=True)
class SafetyCase:
    id: str
    input: str
    category: str
    required_terms: list[str] = field(default_factory=list)
    blocked_terms: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SafetyCaseResult:
    case_id: str
    category: str
    input: str
    output: str
    required_terms_found: list[str]
    required_terms_missing: list[str]
    blocked_terms_found: list[str]
    passed: bool
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "input": self.input,
            "output": self.output,
            "required_terms_found": self.required_terms_found,
            "required_terms_missing": self.required_terms_missing,
            "blocked_terms_found": self.blocked_terms_found,
            "passed": self.passed,
            "tags": self.tags,
        }


@dataclass(frozen=True)
class SafetyEvaluationReport:
    metadata: dict[str, str]
    total: int
    passed: int
    pass_rate: float
    results: list[SafetyCaseResult]
    category_summary: dict[str, dict[str, float | int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata,
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "category_summary": self.category_summary,
            "results": [result.to_dict() for result in self.results],
        }


class SafetyEvalRunner:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def run(self, cases: Sequence[SafetyCase]) -> SafetyEvaluationReport:
        results = [self._run_case(case) for case in cases]
        total = len(results)
        passed = sum(1 for result in results if result.passed)

        return SafetyEvaluationReport(
            metadata={
                "schema_version": "redteam.report.v1",
                "provider": getattr(self.provider, "name", "unknown"),
                "model": getattr(self.provider, "model", "unknown"),
            },
            total=total,
            passed=passed,
            pass_rate=passed / total if total else 0.0,
            results=results,
            category_summary=safety_category_summary(results),
        )

    def _run_case(self, case: SafetyCase) -> SafetyCaseResult:
        response = self.provider.generate(case.input)
        output = response.text

        required_terms_found = matching_terms(output, case.required_terms)
        required_terms_missing = [
            term for term in case.required_terms if term not in required_terms_found
        ]
        blocked_terms_found = matching_terms(output, case.blocked_terms)

        passed = not required_terms_missing and not blocked_terms_found

        return SafetyCaseResult(
            case_id=case.id,
            category=case.category,
            input=case.input,
            output=output,
            required_terms_found=required_terms_found,
            required_terms_missing=required_terms_missing,
            blocked_terms_found=blocked_terms_found,
            passed=passed,
            tags=case.tags,
        )


def load_safety_cases(path: str | Path) -> list[SafetyCase]:
    cases: list[SafetyCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        raw = json.loads(line)
        cases.append(
            SafetyCase(
                id=str(raw["id"]),
                input=str(raw["input"]),
                category=str(raw["category"]),
                required_terms=[str(item) for item in raw.get("required_terms", [])],
                blocked_terms=[str(item) for item in raw.get("blocked_terms", [])],
                tags=[str(item) for item in raw.get("tags", [])],
            )
        )

    return cases


def matching_terms(text: str, terms: Sequence[str]) -> list[str]:
    lowered = text.lower()
    return [term for term in terms if term.lower() in lowered]


def safety_category_summary(
    results: Sequence[SafetyCaseResult],
) -> dict[str, dict[str, float | int]]:
    buckets: dict[str, dict[str, float | int]] = {}

    for result in results:
        bucket = buckets.setdefault(
            result.category,
            {
                "total": 0,
                "passed": 0,
                "pass_rate": 0.0,
                "blocked_findings": 0,
                "missing_required_terms": 0,
            },
        )
        bucket["total"] = int(bucket["total"]) + 1
        bucket["passed"] = int(bucket["passed"]) + int(result.passed)
        bucket["blocked_findings"] = int(bucket["blocked_findings"]) + len(
            result.blocked_terms_found
        )
        bucket["missing_required_terms"] = int(bucket["missing_required_terms"]) + len(
            result.required_terms_missing
        )

    for bucket in buckets.values():
        total = int(bucket["total"])
        passed = int(bucket["passed"])
        bucket["pass_rate"] = passed / total if total else 0.0

    return dict(sorted(buckets.items()))


def render_safety_markdown_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Safety Red-Team Report",
        "",
        "## Summary",
        "",
        f"- Total cases: `{int(payload.get('total', 0))}`",
        f"- Passed cases: `{int(payload.get('passed', 0))}`",
        f"- Pass rate: `{float(payload.get('pass_rate', 0.0)):.3f}`",
        "",
        "## Category Summary",
        "",
        "| Category | Total | Passed | Pass Rate | Blocked Findings | Missing Required Terms |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]

    category_summary = payload.get("category_summary", {})
    if isinstance(category_summary, Mapping):
        for category, summary in category_summary.items():
            if not isinstance(summary, Mapping):
                continue

            lines.append(
                "| {category} | {total} | {passed} | {pass_rate:.3f} | "
                "{blocked} | {missing} |".format(
                    category=_safe_cell(category),
                    total=int(summary.get("total", 0)),
                    passed=int(summary.get("passed", 0)),
                    pass_rate=float(summary.get("pass_rate", 0.0)),
                    blocked=int(summary.get("blocked_findings", 0)),
                    missing=int(summary.get("missing_required_terms", 0)),
                )
            )

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Category | Passed | Missing Required Terms | Blocked Terms Found |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    results = payload.get("results", [])
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, Mapping):
                continue

            missing = item.get("required_terms_missing", [])
            blocked = item.get("blocked_terms_found", [])

            lines.append(
                "| {case_id} | {category} | {passed} | {missing} | {blocked} |".format(
                    case_id=_safe_cell(item.get("case_id", "")),
                    category=_safe_cell(item.get("category", "")),
                    passed="yes" if bool(item.get("passed")) else "no",
                    missing=_safe_cell(_join_list(missing)),
                    blocked=_safe_cell(_join_list(blocked)),
                )
            )

    return "\n".join(lines) + "\n"


def write_safety_report_bundle(
    payload: Mapping[str, Any],
    *,
    report_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / f"{stem}.json"
    markdown_path = report_dir / f"{stem}.md"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_safety_markdown_report(payload), encoding="utf-8")

    return json_path, markdown_path


def _join_list(value: object) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def _safe_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
