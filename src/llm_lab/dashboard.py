from __future__ import annotations

import html
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DashboardReport:
    name: str
    report_type: str
    path: str
    pass_rate: float | None
    passed: int | None
    total: int | None
    release_ready: bool | None = None
    gate_passed: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "report_type": self.report_type,
            "path": self.path,
            "pass_rate": self.pass_rate,
            "passed": self.passed,
            "total": self.total,
            "release_ready": self.release_ready,
            "gate_passed": self.gate_passed,
        }


def build_dashboard_payload(
    report_paths: Sequence[str | Path],
    *,
    blocked_report_paths: Sequence[str | Path] = (),
) -> dict[str, Any]:
    reports = [dashboard_report_from_path(Path(path)) for path in report_paths]
    blocked_reports = [dashboard_report_from_path(Path(path)) for path in blocked_report_paths]
    readiness_reports = [report for report in reports if report.report_type == "release-readiness"]
    release_ready = (
        readiness_reports[-1].release_ready
        if readiness_reports and readiness_reports[-1].release_ready is not None
        else all(_report_passed(report) for report in reports)
    )

    return {
        "metadata": {
            "schema_version": "dashboard.report.v1",
            "generated_at_utc": datetime.now(UTC).isoformat(),
        },
        "release_ready": bool(release_ready),
        "total_reports": len(reports),
        "reports": [report.to_dict() for report in reports],
        "blocked_reports": [report.to_dict() for report in blocked_reports],
        "evidence_summary": dashboard_evidence_summary(bool(release_ready), blocked_reports),
        "summary": {
            "evalops_reports": _count_type(reports, "evalops"),
            "rag_reports": _count_type(reports, "rag-evaluation"),
            "safety_reports": _count_type(reports, "safety-redteam"),
            "readiness_reports": _count_type(reports, "release-readiness"),
        },
    }


def dashboard_evidence_summary(
    release_ready: bool,
    blocked_reports: Sequence[DashboardReport],
) -> list[dict[str, str]]:
    rows = [
        {
            "evidence_type": "Current release candidate",
            "status": "READY" if release_ready else "NOT READY",
            "detail": (
                "Aggregated EvalOps, RAG, safety, and readiness reports for the current candidate."
            ),
            "path": "",
        }
    ]

    for report in blocked_reports:
        blocked = not _report_passed(report)
        rows.append(
            {
                "evidence_type": "Controlled blocked-release scenario",
                "status": "BLOCKED AS EXPECTED" if blocked else "UNEXPECTED PASS",
                "detail": (
                    f"{report.name}: pass_rate={_format_optional_rate(report.pass_rate)}; "
                    "expected missing evidence to fail closed."
                ),
                "path": report.path,
            }
        )

    return rows


def dashboard_report_from_path(path: Path) -> DashboardReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    report_type = infer_dashboard_report_type(payload)

    gate = payload.get("gate")
    gate_passed = None
    if isinstance(gate, Mapping) and "passed" in gate:
        gate_passed = bool(gate["passed"])

    release_ready = None
    if "release_ready" in payload:
        release_ready = bool(payload["release_ready"])

    return DashboardReport(
        name=path.stem,
        report_type=report_type,
        path=str(path),
        pass_rate=_float_or_none(payload.get("pass_rate")),
        passed=_int_or_none(payload.get("passed")),
        total=_int_or_none(payload.get("total")),
        release_ready=release_ready,
        gate_passed=gate_passed,
    )


def infer_dashboard_report_type(payload: Mapping[str, Any]) -> str:
    metadata = payload.get("metadata", {})
    schema_version = ""
    if isinstance(metadata, Mapping):
        schema_version = str(metadata.get("schema_version", ""))

    if schema_version.startswith("release-readiness."):
        return "release-readiness"
    if schema_version.startswith("redteam."):
        return "safety-redteam"
    if schema_version.startswith("evalops."):
        return "evalops"
    if "avg_recall_at_k" in payload and "avg_groundedness" in payload:
        return "rag-evaluation"
    if "category_summary" in payload:
        return "safety-redteam"
    return "unknown"


def render_dashboard_html(payload: Mapping[str, Any]) -> str:
    release_ready = bool(payload.get("release_ready", False))
    status = "READY" if release_ready else "NOT READY"
    status_class = "ready" if release_ready else "not-ready"

    reports = payload.get("reports", [])
    summary = payload.get("summary", {})
    metadata = payload.get("metadata", {})

    generated_at = ""
    if isinstance(metadata, Mapping):
        generated_at = str(metadata.get("generated_at_utc", ""))

    cards = _summary_cards(summary if isinstance(summary, Mapping) else {})
    rows = _report_rows(reports if isinstance(reports, list) else [])
    evidence_rows = _evidence_rows(payload.get("evidence_summary", []))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LLM EvalOps Lab Dashboard</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0f172a;
      --panel: #111827;
      --panel-2: #1f2937;
      --text: #e5e7eb;
      --muted: #94a3b8;
      --border: #334155;
      --ready: #22c55e;
      --warn: #f97316;
      --accent: #38bdf8;
    }}
    body {{
      margin: 0;
      background: radial-gradient(circle at top left, #1e3a8a 0, var(--bg) 35%);
      color: var(--text);
      font-family:
        Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 48px 24px;
    }}
    .hero {{
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 32px;
      background: rgba(17, 24, 39, 0.82);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.35);
    }}
    .eyebrow {{
      color: var(--accent);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 12px 0 8px;
      font-size: clamp(34px, 6vw, 64px);
      line-height: 1;
    }}
    .subtitle {{
      color: var(--muted);
      max-width: 820px;
      font-size: 18px;
      line-height: 1.65;
    }}
    .status {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      margin-top: 20px;
      padding: 10px 14px;
      border-radius: 999px;
      font-weight: 800;
      border: 1px solid var(--border);
      background: var(--panel-2);
    }}
    .status.ready {{
      color: var(--ready);
    }}
    .status.not-ready {{
      color: var(--warn);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 16px;
      margin: 24px 0;
    }}
    .card {{
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgba(15, 23, 42, 0.78);
      padding: 18px;
    }}
    .card .label {{
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .card .value {{
      margin-top: 10px;
      font-size: 32px;
      font-weight: 800;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      overflow: hidden;
      border-radius: 16px;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid var(--border);
    }}
    th, td {{
      border-bottom: 1px solid var(--border);
      padding: 14px 12px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      background: rgba(31, 41, 55, 0.76);
    }}
    tr:last-child td {{
      border-bottom: 0;
    }}
    code {{
      color: #bfdbfe;
      overflow-wrap: anywhere;
    }}
    .footer {{
      color: var(--muted);
      margin-top: 24px;
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <div class="eyebrow">LLM EvalOps Lab</div>
      <h1>Release Evidence Dashboard</h1>
      <p class="subtitle">
        Portfolio-grade static dashboard for deterministic EvalOps, regression,
        RAG retrieval quality, safety red-team, experiment tracking,
        and release readiness artifacts.
      </p>
      <div class="status {status_class}">Status: {html.escape(status)}</div>
      <div class="grid">
        {cards}
      </div>
      <section class="evidence-panel">
        <h2>Gate Evidence</h2>
        <p class="subtitle small">
          READY reflects the current passing release candidate. Controlled blocked-release
          evidence proves gates fail closed when required retrieval evidence is missing.
        </p>
        <table>
          <thead>
            <tr>
              <th>Evidence Type</th>
              <th>Status</th>
              <th>Detail</th>
              <th>Path</th>
            </tr>
          </thead>
          <tbody>
            {evidence_rows}
          </tbody>
        </table>
      </section>
      <table>
        <thead>
          <tr>
            <th>Report</th>
            <th>Type</th>
            <th>Pass Rate</th>
            <th>Passed / Total</th>
            <th>Gate</th>
            <th>Path</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
      <p class="footer">Generated at: <code>{html.escape(generated_at)}</code></p>
    </section>
  </main>
</body>
</html>
"""


def write_dashboard_bundle(
    payload: Mapping[str, Any],
    *,
    report_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / f"{stem}.json"
    html_path = report_dir / f"{stem}.html"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    html_path.write_text(render_dashboard_html(payload), encoding="utf-8")

    return json_path, html_path


def _summary_cards(summary: Mapping[str, Any]) -> str:
    items = [
        ("EvalOps", summary.get("evalops_reports", 0)),
        ("RAG", summary.get("rag_reports", 0)),
        ("Safety", summary.get("safety_reports", 0)),
        ("Readiness", summary.get("readiness_reports", 0)),
    ]

    return "\n".join(
        (
            '<div class="card">'
            f'<div class="label">{html.escape(label)}</div>'
            f'<div class="value">{int(value)}</div>'
            "</div>"
        )
        for label, value in items
    )


def _evidence_rows(rows: object) -> str:
    if not isinstance(rows, list):
        return ""

    rendered: list[str] = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue

        rendered.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('evidence_type', '')))}</td>"
            f"<td>{html.escape(str(item.get('status', '')))}</td>"
            f"<td>{html.escape(str(item.get('detail', '')))}</td>"
            f"<td><code>{html.escape(str(item.get('path', '')))}</code></td>"
            "</tr>"
        )

    return "\n".join(rendered)


def _report_rows(reports: Sequence[object]) -> str:
    rows: list[str] = []

    for item in reports:
        if not isinstance(item, Mapping):
            continue

        pass_rate = item.get("pass_rate")
        pass_rate_text = "n/a" if pass_rate is None else f"{float(pass_rate):.3f}"

        passed = item.get("passed")
        total = item.get("total")
        passed_total = "n/a" if passed is None or total is None else f"{passed} / {total}"

        gate = item.get("gate_passed")
        gate_text = "n/a" if gate is None else str(bool(gate)).lower()

        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('name', '')))}</td>"
            f"<td>{html.escape(str(item.get('report_type', '')))}</td>"
            f"<td>{html.escape(pass_rate_text)}</td>"
            f"<td>{html.escape(passed_total)}</td>"
            f"<td>{html.escape(gate_text)}</td>"
            f"<td><code>{html.escape(str(item.get('path', '')))}</code></td>"
            "</tr>"
        )

    return "\n".join(rows)


def _format_optional_rate(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _report_passed(report: DashboardReport) -> bool:
    if report.pass_rate is None:
        return False
    if report.pass_rate < 1.0:
        return False
    if report.gate_passed is False:
        return False
    return report.release_ready is not False


def _count_type(reports: Sequence[DashboardReport], report_type: str) -> int:
    return sum(1 for report in reports if report.report_type == report_type)


def _float_or_none(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None
