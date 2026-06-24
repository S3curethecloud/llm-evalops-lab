from llm_lab.metrics import contains_all, exact_match, refusal_detected, token_f1


def test_exact_match_normalizes_spacing_and_case() -> None:
    assert exact_match(" Hello   World ", "hello world")


def test_contains_all_is_case_insensitive() -> None:
    assert contains_all("Retrieval Augmented Generation", ["retrieval", "generation"])


def test_token_f1_has_overlap() -> None:
    assert token_f1("quality and regressions", "quality regressions release readiness") > 0.4


def test_refusal_detected() -> None:
    assert refusal_detected("I cannot help with that request")
