from __future__ import annotations

from typing import Protocol

from llm_lab.schemas import LLMResponse


class LLMProvider(Protocol):
    name: str
    model: str

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> LLMResponse:
        """Generate a model response."""
