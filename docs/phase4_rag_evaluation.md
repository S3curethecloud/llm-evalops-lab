# Phase 4 RAG Evaluation Harness and Retrieval Quality Metrics

Phase 4 adds deterministic retrieval evaluation for RAG systems.

## Scope

Phase 4 adds:

- local RAG corpus fixtures
- RAG eval JSONL dataset
- retrieval recall@k
- context precision
- grounded-term coverage
- per-tag RAG score summaries
- CLI `rag-eval` command
- CI-gated RAG evaluation

## Local RAG eval

```bash
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

Expected outputs:

reports/rag-sample.json
reports/rag-sample.md
Metrics
Metric	Meaning
recall_at_k	Fraction of expected documents retrieved in the top-k results
context_precision	Fraction of retrieved documents that were expected
groundedness	Fraction of expected terms present in retrieved context

This harness tests retrieval quality. It does not claim end-to-end factuality for a live generative answer.
