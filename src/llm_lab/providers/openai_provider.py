from __future__ import annotations

import time
from typing import Any

from llm_lab.config import load_settings
from llm_lab.schemas import LLMResponse


class OpenAIProvider:
    """OpenAI Responses API provider.

    The import is lazy so tests and CI can run without OpenAI credentials.
    """

    name = "openai"

    def __init__(self, model: str | None = None) -> None:
        settings = load_settings()
        self.model = model or settings.openai_model
        self._api_key = settings.openai_api_key

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> LLMResponse:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is required for provider=openai")

        from openai import OpenAI

        client = OpenAI(api_key=self._api_key)
        started = time.perf_counter()
        response = client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "developer",
                    "content": system_prompt or "You are a precise assistant.",
                },
                {"role": "user", "content": prompt},
            ],
        )
        elapsed = (time.perf_counter() - started) * 1000
        return LLMResponse(
            text=_extract_output_text(response),
            model=self.model,
            provider=self.name,
            latency_ms=elapsed,
            raw={"id": getattr(response, "id", None)},
        )


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text:
        return output_text

    output = getattr(response, "output", []) or []
    parts: list[str] = []
    for item in output:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts).strip()
