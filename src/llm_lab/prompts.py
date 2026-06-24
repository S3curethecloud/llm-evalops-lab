from __future__ import annotations

from dataclasses import dataclass


DEFAULT_SYSTEM_PROMPT = """You are a precise, security-aware assistant. Answer directly and do not invent facts."""

DEFAULT_EVAL_TEMPLATE = """Answer the user request with a concise, factual response.

User request: {input}
"""


@dataclass(frozen=True)
class PromptTemplate:
    template: str = DEFAULT_EVAL_TEMPLATE

    def render(self, **kwargs: str) -> str:
        try:
            return self.template.format(**kwargs)
        except KeyError as exc:
            missing = exc.args[0]
            raise ValueError(f"Missing prompt variable: {missing}") from exc
