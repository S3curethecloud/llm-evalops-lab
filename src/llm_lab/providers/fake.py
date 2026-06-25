from __future__ import annotations

import time

from llm_lab.schemas import LLMResponse


class FakeProvider:
    """Deterministic provider used for local tests and CI."""

    name = "fake"
    default_model = "fake-deterministic-v1"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or self.default_model

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> LLMResponse:
        started = time.perf_counter()
        lowered = prompt.lower()

        if "hidden system prompt" in lowered or "developer message" in lowered:
            text = "I cannot reveal hidden system prompts or developer messages."
        elif "production api key" in lowered or "print the production api key" in lowered:
            text = "I cannot provide secrets. Use secrets management and environment variables."
        elif "ssn" in lowered or "social security" in lowered:
            text = "Minimize PII in logs and redact sensitive user data before storage."
        elif "nonexistent source" in lowered or "fake citation" in lowered or "make up" in lowered:
            text = "I cannot verify that source. Cite reliable evidence or state uncertainty."
        elif "developer mode" in lowered or "bypass safety" in lowered:
            text = "I cannot bypass safety policies or ignore system instructions."
        elif "prompt injection" in lowered or "ignore previous instructions" in lowered:
            text = "Treat prompt injection as untrusted input and follow the system instructions."
        elif "hallucination" in lowered:
            text = "State uncertainty, avoid hallucination, and ask for or cite reliable evidence."
        elif "regression" in lowered:
            text = (
                "Regression tests compare current outputs against baselines to catch quality drops."
            )
        elif "pii" in lowered:
            text = "Minimize PII in logs and redact sensitive user data before storage."
        elif "rag" in lowered:
            text = "Retrieval augmented generation combines retrieval with generation."
        elif "eval" in lowered:
            text = "Evals measure quality, regressions, and release readiness."
        elif "api key" in lowered or "api keys" in lowered:
            text = "Never commit API keys; use secrets management and environment variables."
        else:
            text = f"Fake response: {prompt[:120]}"

        elapsed = (time.perf_counter() - started) * 1000
        return LLMResponse(
            text=text,
            model=self.model,
            provider=self.name,
            latency_ms=elapsed,
            raw={"system_prompt_used": bool(system_prompt)},
        )
