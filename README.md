# LLM EvalOps Lab

Engineering-grade LLM evaluation, safety, retrieval, and release-readiness lab for building reliable LLM applications with GitHub-native CI.

Recommended repository name: **`llm-evalops-lab`**

## What this repo gives you

- Provider abstraction for real and fake LLM backends.
- OpenAI provider adapter using the Responses API.
- Deterministic fake provider for unit tests and CI.
- JSONL evaluation datasets.
- Prompt templates with explicit system/user boundaries.
- Core metrics: exact match, token F1, contains-all, refusal detection, latency.
- Safety checks for secrets, PII-like patterns, and blocked text.
- Tiny standard-library RAG index for retrieval experiments.
- CLI for local runs.
- GitHub Actions CI for lint, format check, and tests.
- Docs for architecture, evaluation methodology, and GitHub setup.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
cp .env.example .env
pytest
llm-lab eval --dataset data/sample_dataset.jsonl --provider fake
```

## Run with OpenAI

Set your environment variables:

```bash
export OPENAI_API_KEY='your-key'
export OPENAI_MODEL='gpt-4o-mini'
llm-lab ask --provider openai --input 'Summarize why evals matter for LLM apps.'
```

The default project uses `gpt-4o-mini` as a conservative starter model, but you should set `OPENAI_MODEL` to the model approved for your account and use case.

## Project layout

```text
.
├── .github/workflows/ci.yml
├── configs/eval.default.json
├── data/sample_dataset.jsonl
├── docs/
├── notebooks/README.md
├── scripts/run_eval.py
├── src/llm_lab/
└── tests/
```

## Core workflow

1. Add test cases to `data/*.jsonl`.
2. Edit prompts in `src/llm_lab/prompts.py` or add prompt templates under `configs/`.
3. Run `llm-lab eval` locally with the fake provider first.
4. Run with the OpenAI provider only after secrets are configured.
5. Gate merges through GitHub Actions.

## Dataset format

Each JSONL row is an evaluation case:

```json
{"id":"case-001","input":"What is RAG?","ideal":"retrieval augmented generation","tags":["rag","definition"],"must_include":["retrieval","generation"]}
```

## Commands

```bash
llm-lab ask --provider fake --input 'hello'
llm-lab eval --dataset data/sample_dataset.jsonl --provider fake
llm-lab retrieve --query 'guardrails' --docs docs/architecture.md docs/evaluation.md
```

## Engineering standards

This lab is intentionally structured like a real repository: source package, tests, CI, typed interfaces, docs, safe defaults, deterministic tests, and a provider abstraction so production credentials are never needed for the test suite.

## License

MIT
