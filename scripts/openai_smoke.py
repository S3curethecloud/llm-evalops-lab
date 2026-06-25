from __future__ import annotations

import os
import sys

from llm_lab.providers.openai_provider import OpenAIProvider


def main() -> int:
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set; skipping live OpenAI smoke test.")
        return 0

    response = OpenAIProvider().generate(
        "Return one short sentence confirming this smoke test is working.",
        system_prompt="You are a concise test assistant.",
    )

    print(response.text)

    if not response.text.strip():
        print("OpenAI smoke test failed: empty response.", file=sys.stderr)
        return 1

    if response.latency_ms <= 0:
        print("OpenAI smoke test failed: latency was not recorded.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
