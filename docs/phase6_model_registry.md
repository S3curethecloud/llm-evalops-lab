# Phase 6 Provider Expansion and Configurable Model Registry

Phase 6 adds a model registry layer above providers.

## Scope

Phase 6 adds:

- default model registry config
- model aliases
- explicit `--model` support
- `--model-alias` support
- `--model-registry` override support
- `llm-lab models` command
- provider construction through resolved model selections
- future extension point for local/open-source providers

## List configured models

    llm-lab models

JSON output:

    llm-lab models --format json

## Use a model alias

    llm-lab ask \
      --provider fake \
      --model-alias ci \
      --input "Define RAG in one sentence."

## Use an explicit model

    llm-lab eval \
      --dataset data/sample_dataset.jsonl \
      --provider fake \
      --model fake-deterministic-v1 \
      --report-dir reports \
      --report-stem sample-fake-model

## Use a custom registry

    llm-lab models --registry config/model_registry.json

The registry file may be either a JSON list or a JSON object with a `models` list.
