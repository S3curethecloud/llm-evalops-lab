# Phase 7 Safety and Red-Team Evaluation Suite

Phase 7 adds deterministic safety and red-team evaluation.

## Scope

Phase 7 adds:

- adversarial safety dataset
- prompt-injection checks
- jailbreak checks
- secrets handling checks
- PII logging checks
- hallucination/evidence checks
- required-term and blocked-term scoring
- category summaries
- JSON and Markdown safety reports
- CI-gated red-team pass-rate threshold

## Local run

    llm-lab redteam \
      --dataset data/redteam_dataset.jsonl \
      --provider fake \
      --model-alias ci \
      --min-pass-rate 1.0 \
      --report-dir reports \
      --report-stem redteam-fake

## Metrics

| Metric | Meaning |
|---|---|
| `pass_rate` | Fraction of red-team cases that passed |
| `required_terms_missing` | Safety expectations not found in the output |
| `blocked_terms_found` | Unsafe or disallowed terms found in the output |
| `category_summary` | Per-category safety result breakdown |

This suite is deterministic and CI-safe. It is not a replacement for a full human red-team review.
