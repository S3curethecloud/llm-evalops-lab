from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    report_type: str
    report_path: str
    pass_rate: float | None
    gate_passed: bool | None
    passed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "report_type": self.report_type,
            "report_path": self.report_path,
            "pass_rate": self.pass_rate,
            "gate_passed": self.gate_passed,
            "passed": self.passed,
            "reason": self.reason,
        }


def build_readiness_payload(
    report_paths: Sequence[str | Path],
    *,
    min_pass_rate: float = 1.0,
) -> dict[str, Any]:
    checks = [
        readiness_check_from_report(Path(path), min_pass_rate=min_pass_rate)
        for path in report_paths
    ]
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)

    return {
        "metadata": {
            "schema_version": "release-readiness.report.v1",
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "min_pass_rate": min_pass_rate,
        },
        "total": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0.0,
        "release_ready": total > 0 and passed == total,
        "checks": [check.to_dict() for check in checks],
    }


def readiness_check_from_report(
    report_path: Path,
    *,
    min_pass_rate: float = 1.0,
) -> ReadinessCheck:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    report_type = infer_report_type(payload)
    pass_rate = _numeric_or_none(payload.get("pass_rate"))
    gate_passed = infer_gate_status(payload)

    failed_reasons: list[str] = []
    if pass_rate is None:
        failed_reasons.append("report has no numeric pass_rate")
    elif pass_rate < min_pass_rate:
        failed_reasons.append(f"pass_rate {pass_rate:.3f} is below {min_pass_rate:.3f}")

    if gate_passed is False:
        failed_reasons.append("report gate failed")

    passed = not failed_reasons
    reason = "ready" if passed else "; ".join(failed_reasons)

    return ReadinessCheck(
        name=report_path.stem,
        report_type=report_type,
        report_path=str(report_path),
        pass_rate=pass_rate,
        gate_passed=gate_passed,
        passed=passed,
        reason=reason,
    )


def infer_report_type(payload: Mapping[str, Any]) -> str:
    metadata = payload.get("metadata", {})
    schema_version = ""
    if isinstance(metadata, Mapping):
        schema_version = str(metadata.get("schema_version", ""))

    if schema_version.startswith("redteam."):
        return "safety-redteam"
    if schema_version.startswith("evalops."):
        return "evalops"
    if "avg_recall_at_k" in payload and "avg_groundedness" in payload:
        return "rag-evaluation"
    if "category_summary" in payload:
        return "safety-redteam"
    return "unknown"


def infer_gate_status(payload: Mapping[str, Any]) -> bool | None:
    gate = payload.get("gate")
    if isinstance(gate, Mapping) and "passed" in gate:
        return bool(gate["passed"])
    return None


def render_readiness_markdown(payload: Mapping[str, Any]) -> str:
    metadata = payload.get("metadata", {})
    min_pass_rate = 1.0
    if isinstance(metadata, Mapping):
        min_pass_rate = float(metadata.get("min_pass_rate", 1.0))

    release_ready = bool(payload.get("release_ready", False))
    status = "READY" if release_ready else "NOT READY"

    lines = [
        "# Release Readiness Dashboard",
        "",
        "## Summary",
        "",
        f"- Status: `{status}`",
        f"- Total checks: `{int(payload.get('total', 0))}`",
        f"- Passed checks: `{int(payload.get('passed', 0))}`",
        f"- Check pass rate: `{float(payload.get('pass_rate', 0.0)):.3f}`",
        f"- Minimum report pass rate: `{min_pass_rate:.3f}`",
        "",
        "## Checks",
        "",
        "| Check | Type | Report Pass Rate | Gate | Status | Reason |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]

    checks = payload.get("checks", [])
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, Mapping):
                continue

            pass_rate = check.get("pass_rate")
            pass_rate_text = "n/a" if pass_rate is None else f"{float(pass_rate):.3f}"
            gate = check.get("gate_passed")
            gate_text = "n/a" if gate is None else str(bool(gate)).lower()
            status_text = "pass" if bool(check.get("passed")) else "fail"

            lines.append(
                "| {name} | {report_type} | {pass_rate} | {gate} | {status} | {reason} |".format(
                    name=_safe_cell(check.get("name", "")),
                    report_type=_safe_cell(check.get("report_type", "")),
                    pass_rate=pass_rate_text,
                    gate=gate_text,
                    status=status_text,
                    reason=_safe_cell(check.get("reason", "")),
                )
            )

    lines.extend(
        [
            "",
            "## Portfolio Narrative",
            "",
            "This release readiness dashboard aggregates deterministic EvalOps, "
            "RAG, regression, experiment tracking, and safety red-team evidence. "
            "It is intended as a portfolio-grade release summary, not a substitute "
            "for production monitoring or human governance review.",
        ]
    )

    return "\n".join(lines) + "\n"


def write_readiness_bundle(
    payload: Mapping[str, Any],
    *,
    report_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / f"{stem}.json"
    markdown_path = report_dir / f"{stem}.md"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_readiness_markdown(payload), encoding="utf-8")

    return json_path, markdown_path


def _numeric_or_none(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _safe_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
