from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SYSTEM_PROMPT = """You are a precise, security-aware assistant.
Answer directly and do not invent facts."""

DEFAULT_EVAL_TEMPLATE = """Answer the user request with a concise, factual response.

User request:
{input}
"""


@dataclass(frozen=True)
class PromptTemplate:
    system: str = DEFAULT_SYSTEM_PROMPT
    user_template: str = DEFAULT_EVAL_TEMPLATE

    def render_user(self, **kwargs: str) -> str:
        return self.user_template.format(**kwargs)

    def render(self, **kwargs: str) -> str:
        return self.render_user(**kwargs)


DEFAULT_EVAL_PROMPT = PromptTemplate(
    system=DEFAULT_SYSTEM_PROMPT,
    user_template=DEFAULT_EVAL_TEMPLATE,
)
