from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class ExperimentRecord:
    run_id: str
    created_at_utc: str
    provider: str
    model: str
    dataset: str
    report_path: str
    total: int
    passed: int
    pass_rate: float
    avg_latency_ms: float
    gate_passed: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at_utc": self.created_at_utc,
            "provider": self.provider,
            "model": self.model,
            "dataset": self.dataset,
            "report_path": self.report_path,
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "avg_latency_ms": self.avg_latency_ms,
            "gate_passed": self.gate_passed,
        }


def make_run_id(prefix: str = "run") -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid4().hex[:8]
    return f"{prefix}-{timestamp}-{suffix}"


def load_json_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def experiment_record_from_payload(
    payload: Mapping[str, Any],
    *,
    report_path: str | Path,
) -> ExperimentRecord:
    metadata = payload.get("metadata", {})
    if not isinstance(metadata, Mapping):
        metadata = {}

    gate = payload.get("gate")
    gate_passed = bool(gate.get("passed")) if isinstance(gate, Mapping) else None

    return ExperimentRecord(
        run_id=str(metadata.get("run_id", make_run_id("eval"))),
        created_at_utc=str(metadata.get("generated_at_utc", datetime.now(UTC).isoformat())),
        provider=str(metadata.get("provider", "unknown")),
        model=str(metadata.get("model", metadata.get("provider", "unknown"))),
        dataset=str(metadata.get("dataset", "unknown")),
        report_path=str(report_path),
        total=int(payload.get("total", 0)),
        passed=int(payload.get("passed", 0)),
        pass_rate=float(payload.get("pass_rate", 0.0)),
        avg_latency_ms=float(payload.get("avg_latency_ms", 0.0)),
        gate_passed=gate_passed,
    )


def append_experiment_record(
    payload: Mapping[str, Any],
    registry_path: Path,
    *,
    report_path: str | Path,
) -> ExperimentRecord:
    record = experiment_record_from_payload(payload, report_path=report_path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)

    with registry_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")

    return record


def records_from_reports(report_paths: Sequence[str | Path]) -> list[ExperimentRecord]:
    return [
        experiment_record_from_payload(load_json_report(path), report_path=path)
        for path in report_paths
    ]


def render_scoreboard_csv(records: Iterable[ExperimentRecord]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "run_id",
            "provider",
            "model",
            "dataset",
            "pass_rate",
            "passed",
            "total",
            "avg_latency_ms",
            "gate_passed",
            "report_path",
            "created_at_utc",
        ],
    )
    writer.writeheader()

    for record in records:
        writer.writerow(record.to_dict())

    return output.getvalue()


def render_scoreboard_markdown(records: Sequence[ExperimentRecord]) -> str:
    lines = [
        "# Model Comparison Scoreboard",
        "",
        "| Run ID | Provider | Model | Dataset | Pass Rate | Passed | Total | Gate |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]

    for record in records:
        gate = "n/a" if record.gate_passed is None else str(record.gate_passed).lower()
        lines.append(
            "| {run_id} | {provider} | {model} | {dataset} | "
            "{pass_rate:.3f} | {passed} | {total} | {gate} |".format(
                run_id=_safe_cell(record.run_id),
                provider=_safe_cell(record.provider),
                model=_safe_cell(record.model),
                dataset=_safe_cell(record.dataset),
                pass_rate=record.pass_rate,
                passed=record.passed,
                total=record.total,
                gate=gate,
            )
        )

    return "\n".join(lines) + "\n"


def write_scoreboards(
    report_paths: Sequence[str | Path],
    *,
    csv_path: Path,
    markdown_path: Path,
) -> tuple[Path, Path]:
    records = records_from_reports(report_paths)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)

    csv_path.write_text(render_scoreboard_csv(records), encoding="utf-8")
    markdown_path.write_text(render_scoreboard_markdown(records), encoding="utf-8")

    return csv_path, markdown_path


def _safe_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
