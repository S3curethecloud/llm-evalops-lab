from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RegressionGateResult:
    passed: bool
    reasons: list[str]
    current_pass_rate: float
    min_pass_rate: float
    baseline_pass_rate: float | None = None
    pass_rate_delta: float | None = None
    allowed_regression: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "reasons": self.reasons,
            "current_pass_rate": self.current_pass_rate,
            "min_pass_rate": self.min_pass_rate,
            "baseline_pass_rate": self.baseline_pass_rate,
            "pass_rate_delta": self.pass_rate_delta,
            "allowed_regression": self.allowed_regression,
        }


def load_report(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def tag_summary_from_results(
    results: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, float | int]]:
    buckets: dict[str, dict[str, float | int]] = {}

    for item in results:
        tags = item.get("tags", [])
        if not isinstance(tags, list):
            continue

        passed = bool(item.get("passed"))
        metrics = item.get("metrics", {})
        token_f1 = 0.0
        if isinstance(metrics, Mapping):
            token_f1 = float(metrics.get("token_f1", 0.0))

        for tag in tags:
            tag_name = str(tag)
            bucket = buckets.setdefault(
                tag_name,
                {
                    "total": 0,
                    "passed": 0,
                    "pass_rate": 0.0,
                    "avg_token_f1": 0.0,
                },
            )
            bucket["total"] = int(bucket["total"]) + 1
            bucket["passed"] = int(bucket["passed"]) + int(passed)
            bucket["avg_token_f1"] = float(bucket["avg_token_f1"]) + token_f1

    for bucket in buckets.values():
        total = int(bucket["total"])
        passed = int(bucket["passed"])
        token_f1_total = float(bucket["avg_token_f1"])
        bucket["pass_rate"] = passed / total if total else 0.0
        bucket["avg_token_f1"] = token_f1_total / total if total else 0.0

    return dict(sorted(buckets.items()))


def gate_payload(
    payload: Mapping[str, Any],
    *,
    min_pass_rate: float,
    baseline: Mapping[str, Any] | None = None,
    allowed_regression: float = 0.0,
) -> RegressionGateResult:
    current_pass_rate = float(payload.get("pass_rate", 0.0))
    reasons: list[str] = []

    if current_pass_rate < min_pass_rate:
        reasons.append(f"pass_rate {current_pass_rate:.3f} is below minimum {min_pass_rate:.3f}")

    baseline_pass_rate: float | None = None
    pass_rate_delta: float | None = None

    if baseline is not None:
        baseline_pass_rate = float(baseline.get("pass_rate", 0.0))
        pass_rate_delta = current_pass_rate - baseline_pass_rate

        if pass_rate_delta < -allowed_regression:
            reasons.append(
                "pass_rate delta "
                f"{pass_rate_delta:.3f} is below allowed regression "
                f"{-allowed_regression:.3f}"
            )

    return RegressionGateResult(
        passed=not reasons,
        reasons=reasons,
        current_pass_rate=current_pass_rate,
        min_pass_rate=min_pass_rate,
        baseline_pass_rate=baseline_pass_rate,
        pass_rate_delta=pass_rate_delta,
        allowed_regression=allowed_regression,
    )
