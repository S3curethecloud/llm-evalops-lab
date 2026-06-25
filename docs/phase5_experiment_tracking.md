# Phase 5 Experiment Tracking and Model Comparison Matrix

Phase 5 adds lightweight experiment tracking for evaluation reports.

## Scope

Phase 5 adds:

- generated run IDs
- model/provider metadata in eval reports
- JSONL experiment registry
- CSV scoreboards
- Markdown scoreboards
- `llm-lab compare` command
- CI-generated model comparison artifacts

## Local run

Generate two deterministic reports and a scoreboard:

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

## Registry policy

The local registry is written as JSONL. Generated registry files are artifacts, not source.

The tracked source code defines how to generate registry entries; the generated run history remains local or CI-artifact scoped unless intentionally promoted.
