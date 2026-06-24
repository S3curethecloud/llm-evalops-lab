from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class Trace:
    trace_id: str
    name: str
    started_at: float


@contextmanager
def trace(name: str) -> Iterator[Trace]:
    item = Trace(trace_id=str(uuid.uuid4()), name=name, started_at=time.time())
    yield item


def append_jsonl(path: str | Path, payload: dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
