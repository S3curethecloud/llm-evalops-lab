# Architecture

The lab is split into five layers:

1. **Provider layer**: isolates model vendors from the evaluation framework.
2. **Prompt layer**: keeps system and user prompts explicit and reviewable.
3. **Evaluation layer**: runs datasets, collects model outputs, and computes metrics.
4. **Safety layer**: detects obvious secret leakage, PII-like content, and blocked phrases.
5. **Retrieval layer**: provides a tiny local retrieval index for RAG experiments.

## Provider design

All providers implement the same protocol:

```python
response = provider.generate(prompt, system_prompt="...")
```

The fake provider makes tests deterministic. The OpenAI provider is optional at runtime and only imports the SDK when selected.

## Reliability goals

- Evaluation datasets are files under version control.
- CI does not require external API keys.
- Safety checks run before metric aggregation.
- Prompt changes are diffable and reviewable.
- The CLI produces machine-readable JSON reports.
