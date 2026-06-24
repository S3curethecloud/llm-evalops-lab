from llm_lab.rag.index import Document, TokenIndex


def test_retrieval_ranks_relevant_doc_first() -> None:
    index = TokenIndex(
        [
            Document("a", "LLM guardrails and safety checks", {}),
            Document("b", "Banana bread recipe", {}),
        ]
    )
    results = index.search("safety guardrails")
    assert results[0].document.id == "a"
    assert results[0].score > results[1].score
