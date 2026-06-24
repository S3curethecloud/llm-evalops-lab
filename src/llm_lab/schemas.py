from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    provider: str
    latency_ms: float
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvalCase:
    id: str
    input: str
    ideal: str
    tags: list[str] = field(default_factory=list)
    must_include: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    input: str
    ideal: str
    output: str
    passed: bool
    metrics: dict[str, float | bool | str]
    tags: list[str]
    latency_ms: float


@dataclass(frozen=True)
class EvaluationReport:
    total: int
    passed: int
    pass_rate: float
    avg_latency_ms: float
    results: list[CaseResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "results": [
                {
                    "case_id": item.case_id,
                    "input": item.input,
                    "ideal": item.ideal,
                    "output": item.output,
                    "passed": item.passed,
                    "metrics": item.metrics,
                    "tags": item.tags,
                    "latency_ms": item.latency_ms,
                }
                for item in self.results
            ],
        }
