# Phase 2 EvalOps Reporting and Smoke Gate

Phase 2 adds report generation and an optional live-provider smoke gate.

## Scope

Phase 2 adds:

- JSON evaluation report artifacts.
- Markdown evaluation report summaries.
- `reports/` output generation.
- GitHub Actions artifact upload.
- Optional live OpenAI smoke test.
- Deterministic CI as the required quality gate.

## Deterministic local run

```bash
ruff check .
ruff format --check .
pytest
llm-lab eval \
  --dataset data/sample_dataset.jsonl \
  --provider fake \
  --report-dir reports \
  --report-stem fake-sample

Expected report outputs:

reports/fake-sample.json
reports/fake-sample.md
Optional live OpenAI smoke test

The live smoke test is intentionally opt-in. It requires OPENAI_API_KEY.

export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o-mini"
python scripts/openai_smoke.py

The smoke test verifies that the provider can return a non-empty response and records latency. It is not a quality benchmark.

GitHub Actions behavior

The CI workflow has two paths:

Deterministic CI on push and pull request.
Manual OpenAI smoke test through workflow_dispatch.

This avoids requiring secrets for normal pull requests while preserving a real-provider readiness gate.
