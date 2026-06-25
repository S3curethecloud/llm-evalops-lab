from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llm_lab.regression import tag_summary_from_results
from llm_lab.schemas import EvaluationReport

REPORT_SCHEMA_VERSION = "evalops.report.v2"


def report_payload(
    report: EvaluationReport,
    *,
    dataset: str,
    provider: str,
) -> dict[str, Any]:
    payload = report.to_dict()
    results = payload.get("results", [])
    payload["metadata"] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "dataset": dataset,
        "provider": provider,
    }
    payload["tag_summary"] = tag_summary_from_results(results) if isinstance(results, list) else {}
    return payload


def render_markdown_report(payload: Mapping[str, Any]) -> str:
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {}

    total = int(payload.get("total", 0))
    passed = int(payload.get("passed", 0))
    pass_rate = float(payload.get("pass_rate", 0.0))
    avg_latency_ms = float(payload.get("avg_latency_ms", 0.0))

    lines = [
        "# LLM EvalOps Evaluation Report",
        "",
        "## Summary",
        "",
        f"- Schema: `{metadata.get('schema_version', 'unknown')}`",
        f"- Generated UTC: `{metadata.get('generated_at_utc', 'unknown')}`",
        f"- Dataset: `{metadata.get('dataset', 'unknown')}`",
        f"- Provider: `{metadata.get('provider', 'unknown')}`",
        f"- Total cases: `{total}`",
        f"- Passed cases: `{passed}`",
        f"- Pass rate: `{pass_rate:.3f}`",
        f"- Average latency ms: `{avg_latency_ms:.3f}`",
    ]

    gate = payload.get("gate")
    if isinstance(gate, Mapping):
        reasons = gate.get("reasons", [])
        reason_text = ", ".join(str(reason) for reason in reasons) if reasons else "none"
        lines.extend(
            [
                "",
                "## Regression Gate",
                "",
                f"- Passed: `{'yes' if bool(gate.get('passed')) else 'no'}`",
                f"- Minimum pass rate: `{float(gate.get('min_pass_rate', 0.0)):.3f}`",
                f"- Current pass rate: `{float(gate.get('current_pass_rate', 0.0)):.3f}`",
                f"- Baseline pass rate: `{_optional_float(gate.get('baseline_pass_rate'))}`",
                f"- Pass-rate delta: `{_optional_float(gate.get('pass_rate_delta'))}`",
                f"- Allowed regression: `{float(gate.get('allowed_regression', 0.0)):.3f}`",
                f"- Reasons: `{_safe_cell(reason_text)}`",
            ]
        )

    tag_summary = payload.get("tag_summary", {})
    if isinstance(tag_summary, Mapping) and tag_summary:
        lines.extend(
            [
                "",
                "## Tag Summary",
                "",
                "| Tag | Total | Passed | Pass Rate | Avg Token F1 |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for tag, summary in tag_summary.items():
            if not isinstance(summary, Mapping):
                continue
            lines.append(
                "| {tag} | {total} | {passed} | {pass_rate:.3f} | {avg_token_f1:.3f} |".format(
                    tag=_safe_cell(tag),
                    total=int(summary.get("total", 0)),
                    passed=int(summary.get("passed", 0)),
                    pass_rate=float(summary.get("pass_rate", 0.0)),
                    avg_token_f1=float(summary.get("avg_token_f1", 0.0)),
                )
            )

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Passed | Token F1 | Safety Findings | Latency ms | Tags |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )

    results = payload.get("results", [])
    if not isinstance(results, list):
        results = []

    for item in results:
        if not isinstance(item, Mapping):
            continue

        metrics = item.get("metrics", {})
        if not isinstance(metrics, Mapping):
            metrics = {}

        tags = item.get("tags", [])
        tag_text = ", ".join(str(tag) for tag in tags) if isinstance(tags, list) else ""

        lines.append(
            "| {case_id} | {passed} | {token_f1:.3f} | {safety} | {latency:.3f} | {tags} |".format(
                case_id=_safe_cell(item.get("case_id", "")),
                passed="yes" if bool(item.get("passed")) else "no",
                token_f1=float(metrics.get("token_f1", 0.0)),
                safety=_safe_cell(metrics.get("safety_findings", 0)),
                latency=float(item.get("latency_ms", 0.0)),
                tags=_safe_cell(tag_text),
            )
        )

    return "\n".join(lines) + "\n"


def write_json_report(payload: Mapping[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def write_markdown_report(payload: Mapping[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(payload), encoding="utf-8")
    return output_path


def write_report_bundle(
    report: EvaluationReport,
    *,
    report_dir: Path,
    dataset: str,
    provider: str,
    stem: str = "eval-report",
) -> tuple[Path, Path]:
    payload = report_payload(report, dataset=dataset, provider=provider)
    json_path = report_dir / f"{stem}.json"
    markdown_path = report_dir / f"{stem}.md"

    write_json_report(payload, json_path)
    write_markdown_report(payload, markdown_path)

    return json_path, markdown_path


def _optional_float(value: object) -> str:
    if value is None:
        return "none"
    return f"{float(value):.3f}"


def _safe_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
