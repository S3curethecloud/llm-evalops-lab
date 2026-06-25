# Phase 3 Dataset Expansion and Regression Gate

Phase 3 adds richer deterministic datasets and a regression gate for release readiness.

## Scope

Phase 3 adds:

- Expanded deterministic evaluation dataset.
- Per-tag score summaries.
- `--min-pass-rate` CLI gate.
- Baseline report comparison.
- `--allowed-regression` threshold.
- CI failure when pass rate falls below the required threshold.
- CI failure when the current report regresses below the stored baseline.

## Local deterministic gate

```bash
llm-lab eval \
  --dataset data/expanded_dataset.jsonl \
  --provider fake \
  --min-pass-rate 1.0 \
  --baseline-report baselines/fake-expanded-baseline.json \
  --allowed-regression 0.0 \
  --report-dir reports \
  --report-stem expanded-fake

Expected behavior:

command exits 0 when the gate passes
command exits 1 when pass rate falls below threshold
command exits 1 when the current report regresses below the baseline
Baseline policy

The baseline file is intentionally small and stable:

baselines/fake-expanded-baseline.json

Update the baseline only when a change is intentionally accepted and reviewed.
