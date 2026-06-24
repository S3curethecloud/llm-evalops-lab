from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency fallback
    load_dotenv = None  # type: ignore[assignment]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    openai_model: str
    log_path: Path


def load_settings() -> Settings:
    if load_dotenv is not None:
        load_dotenv()

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        log_path=Path(os.getenv("LLM_LAB_LOG_PATH", "artifacts/runs.jsonl")),
    )
