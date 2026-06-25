from llm_lab.rag.eval import RAGEvaluator, load_rag_eval_cases
from llm_lab.rag.index import TokenIndex


def test_controlled_rag_failure_blocks_release_candidate() -> None:
    cases = load_rag_eval_cases("data/rag_failure_dataset.jsonl")
    index = TokenIndex.from_paths(
        [
            "data/rag_corpus/rag.md",
            "data/rag_corpus/evals.md",
        ]
    )

    report = RAGEvaluator(index, top_k=2).run(cases)

    assert report.total == 1
    assert report.pass_rate == 0.0
    assert report.results[0].recall_at_k == 0.0
    assert report.results[0].groundedness == 0.0
    assert report.results[0].passed is False
