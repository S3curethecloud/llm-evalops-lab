# Phase 8 Release Readiness Dashboard and Portfolio Packaging

Phase 8 adds a release readiness dashboard that aggregates evidence from prior phases.

## Scope

Phase 8 adds:

- release readiness report schema
- readiness aggregation across EvalOps reports
- readiness aggregation across RAG reports
- readiness aggregation across safety red-team reports
- Markdown release dashboard
- JSON release dashboard
- CI-generated release readiness artifacts
- portfolio-grade completion narrative

## Local run

Generate the prerequisite reports, then run:

    llm-lab readiness \
      --reports \
        reports/sample-fake.json \
        reports/expanded-fake.json \
        reports/rag-sample.json \
        reports/redteam-fake.json \
      --min-pass-rate 1.0 \
      --report-dir reports \
      --report-stem release-readiness

## Meaning

A release is marked ready when all supplied reports meet the minimum pass-rate threshold and all explicit gates pass.

This dashboard is portfolio-grade release evidence. It is not a replacement for production observability, security review, human red-team review, or compliance certification.
