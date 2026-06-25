from pathlib import Path

from llm_lab.rag.eval import (
    RAGEvaluator,
    grounded_terms,
    load_rag_eval_cases,
    retrieval_context_precision,
    retrieval_recall_at_k,
    write_rag_report_bundle,
)
from llm_lab.rag.index import TokenIndex


def test_retrieval_recall_at_k() -> None:
    assert (
        retrieval_recall_at_k(
            ["doc-a", "doc-b"],
            expected_doc_ids=["doc-b", "doc-c"],
        )
        == 0.5
    )


def test_retrieval_context_precision() -> None:
    assert (
        retrieval_context_precision(
            ["doc-a", "doc-b", "doc-c"],
            expected_doc_ids=["doc-b"],
        )
        == 1 / 3
    )


def test_grounded_terms() -> None:
    assert grounded_terms(
        "Use secrets management and environment variables.", ["secrets management"]
    ) == ["secrets management"]


def test_rag_evaluator_passes_sample_dataset(tmp_path: Path) -> None:
    docs = [
        "data/rag_corpus/rag.md",
        "data/rag_corpus/evals.md",
        "data/rag_corpus/security.md",
        "data/rag_corpus/safety.md",
    ]
    cases = load_rag_eval_cases("data/rag_eval_dataset.jsonl")
    report = RAGEvaluator(TokenIndex.from_paths(docs), top_k=2).run(cases)

    assert report.total == 5
    assert report.pass_rate == 1.0
    assert report.avg_recall_at_k == 1.0
    assert "security" in report.tag_summary

    json_path, markdown_path = write_rag_report_bundle(
        report.to_dict(),
        report_dir=tmp_path,
        stem="rag-sample",
    )

    assert json_path.exists()
    assert markdown_path.exists()
    assert "RAG Evaluation Report" in markdown_path.read_text(encoding="utf-8")
