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

## Phase 2 EvalOps reporting

Generate JSON and Markdown reports locally:

```bash
llm-lab eval \
  --dataset data/sample_dataset.jsonl \
  --provider fake \
  --report-dir reports \
  --report-stem fake-sample

The generated files are ignored by Git by default:

reports/fake-sample.json
reports/fake-sample.md

Run the optional live OpenAI smoke gate only after configuring secrets:

export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o-mini"
python scripts/openai_smoke.py

See docs/phase2_evalops.md for the Phase 2 runbook.

Phase 3 Regression Gate

Run the expanded deterministic regression gate:

llm-lab eval \
  --dataset data/expanded_dataset.jsonl \
  --provider fake \
  --min-pass-rate 1.0 \
  --baseline-report baselines/fake-expanded-baseline.json \
  --allowed-regression 0.0 \
  --report-dir reports \
  --report-stem expanded-fake

This command fails if the current pass rate drops below the minimum threshold or below the stored baseline beyond the allowed regression margin.

See docs/phase3_regression_gate.md for the Phase 3 runbook.

Phase 4 RAG Evaluation

Run the deterministic RAG retrieval quality gate:

llm-lab rag-eval \
  --dataset data/rag_eval_dataset.jsonl \
  --docs \
    data/rag_corpus/rag.md \
    data/rag_corpus/evals.md \
    data/rag_corpus/security.md \
    data/rag_corpus/safety.md \
  --top-k 2 \
  --min-pass-rate 1.0 \
  --report-dir reports \
  --report-stem rag-sample

This command checks retrieval recall, context precision, grounded-term coverage, and per-tag RAG summaries.

See docs/phase4_rag_evaluation.md for the Phase 4 runbook.

## Phase 5 Experiment Tracking

Generate model/provider comparison scoreboards:

    llm-lab eval \
      --dataset data/sample_dataset.jsonl \
      --provider fake \
      --report-dir reports \
      --report-stem sample-fake \
      --registry experiments/registry.jsonl

    llm-lab eval \
      --dataset data/expanded_dataset.jsonl \
      --provider fake \
      --min-pass-rate 1.0 \
      --baseline-report baselines/fake-expanded-baseline.json \
      --allowed-regression 0.0 \
      --report-dir reports \
      --report-stem expanded-fake \
      --registry experiments/registry.jsonl

    llm-lab compare \
      --reports reports/sample-fake.json reports/expanded-fake.json \
      --output-csv reports/model-comparison.csv \
      --output-md reports/model-comparison.md

See `docs/phase5_experiment_tracking.md` for the Phase 5 runbook.
