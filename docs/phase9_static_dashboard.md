# Phase 9 Static Demo Dashboard

Phase 9 adds a zero-dependency static HTML dashboard for portfolio demos.

## Scope

Phase 9 adds:

- `llm-lab dashboard` command
- static HTML dashboard output
- dashboard JSON manifest
- report type inference
- summary cards for EvalOps, RAG, safety, and readiness reports
- release readiness status display
- CI-generated dashboard artifact

## Local run

Generate reports first, then run:

    llm-lab dashboard \
      --reports \
        reports/sample-fake.json \
        reports/expanded-fake.json \
        reports/rag-sample.json \
        reports/redteam-fake.json \
        reports/release-readiness.json \
      --report-dir reports \
      --report-stem dashboard

Open the generated file:

    reports/dashboard.html

Optional local server:

    python -m http.server 8000 --directory reports

Then open:

    http://localhost:8000/dashboard.html

## Design choice

This phase intentionally avoids adding a web framework dependency. The generated dashboard is static, reviewable, portable, and CI-artifact friendly.
