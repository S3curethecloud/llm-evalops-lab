from llm_lab.dataset import load_jsonl
from llm_lab.evals import EvalRunner
from llm_lab.providers.fake import FakeProvider


def test_eval_runner_passes_sample_dataset() -> None:
    cases = load_jsonl("data/sample_dataset.jsonl")
    report = EvalRunner(FakeProvider()).run(cases)
    assert report.total == 3
    assert report.pass_rate == 1.0
