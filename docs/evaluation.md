# Evaluation methodology

This lab starts with lightweight deterministic metrics and leaves room for model-graded or human-reviewed evals later.

## Metrics

- **contains_all**: checks whether required substrings appear in the output.
- **exact_match**: strict normalized text equality.
- **token_f1**: overlap between ideal answer tokens and model output tokens.
- **refusal_detected**: identifies common refusal patterns.
- **latency_ms**: basic runtime measurement per case.

## Release gate

A production workflow should block merges if:

- pass rate drops below threshold,
- safety violations increase,
- average latency exceeds budget,
- new prompt changes lack eval coverage.

## Extending evals

Add new metrics in `src/llm_lab/metrics.py` and register them in `src/llm_lab/evals.py`.
