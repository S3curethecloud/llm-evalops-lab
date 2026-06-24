from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from llm_lab.schemas import EvalCase


class DatasetError(ValueError):
    """Raised when an evaluation dataset is invalid."""


def load_jsonl(path: str | Path) -> list[EvalCase]:
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise DatasetError(f"Dataset not found: {dataset_path}")

    cases: list[EvalCase] = []
    with dataset_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise DatasetError(f"Invalid JSON on line {line_number}: {exc}") from exc
            cases.append(_case_from_payload(payload, line_number))
    if not cases:
        raise DatasetError(f"Dataset contains no cases: {dataset_path}")
    return cases


def dump_results_jsonl(path: str | Path, rows: Iterable[dict[str, object]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _case_from_payload(payload: dict[str, object], line_number: int) -> EvalCase:
    required = ["id", "input", "ideal"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise DatasetError(f"Line {line_number} missing required fields: {missing}")

    return EvalCase(
        id=_as_str(payload["id"], "id", line_number),
        input=_as_str(payload["input"], "input", line_number),
        ideal=_as_str(payload["ideal"], "ideal", line_number),
        tags=_as_str_list(payload.get("tags", []), "tags", line_number),
        must_include=_as_str_list(payload.get("must_include", []), "must_include", line_number),
    )


def _as_str(value: object, field_name: str, line_number: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DatasetError(f"Line {line_number} field {field_name!r} must be a non-empty string")
    return value


def _as_str_list(value: object, field_name: str, line_number: int) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise DatasetError(f"Line {line_number} field {field_name!r} must be a list of strings")
    return value
