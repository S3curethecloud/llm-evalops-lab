# Phase 10 Failure Evidence and Gate-Blocked Scenario

Phase 10 adds a controlled failure scenario to demonstrate that the release gates are not decorative.

## Purpose

The public dashboard shows the current passing release candidate. That is intentional.

This phase adds a separate blocked-release scenario that proves the framework catches failures when required evidence is missing.

## Scenario

A RAG evaluation case asks:

    How should API keys be handled?

The case expects:

    data/rag_corpus/security.md

The controlled failure run intentionally omits that document from the retrieval corpus:

    data/rag_corpus/rag.md
    data/rag_corpus/evals.md

Expected result:

- recall@k drops below threshold
- groundedness drops below threshold
- pass rate is `0.0`
- `llm-lab rag-eval` exits non-zero
- CI treats that non-zero result as the expected blocked-release behavior

## Local run

This command is expected to fail:

    llm-lab rag-eval \
      --dataset data/rag_failure_dataset.jsonl \
      --docs \
        data/rag_corpus/rag.md \
        data/rag_corpus/evals.md \
      --top-k 2 \
      --min-pass-rate 1.0 \
      --report-dir reports \
      --report-stem rag-blocked-failure

Use this wrapper to assert the failure is intentional:

    if llm-lab rag-eval \
      --dataset data/rag_failure_dataset.jsonl \
      --docs data/rag_corpus/rag.md data/rag_corpus/evals.md \
      --top-k 2 \
      --min-pass-rate 1.0 \
      --report-dir reports \
      --report-stem rag-blocked-failure; then
      echo "Expected controlled RAG failure to fail, but it passed"
      exit 1
    else
      echo "Controlled RAG failure correctly blocked release candidate"
    fi

## Interview framing

The main dashboard shows the current passing deterministic release candidate. The blocked-release scenario exists separately to demonstrate that the gates are meaningful.

The point is not that the synthetic release candidate gets perfect scores. The point is that the framework produces pass/fail evidence, blocks bad releases, and makes release readiness visible.
