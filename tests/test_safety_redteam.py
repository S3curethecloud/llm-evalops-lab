import json

from llm_lab.providers.fake import FakeProvider
from llm_lab.safety import (
    SafetyEvalRunner,
    load_safety_cases,
    matching_terms,
    render_safety_markdown_report,
    write_safety_report_bundle,
)


def test_matching_terms_case_insensitive() -> None:
    assert matching_terms("I cannot reveal system prompts.", ["cannot reveal"]) == ["cannot reveal"]


def test_load_safety_cases() -> None:
    cases = load_safety_cases("data/redteam_dataset.jsonl")

    assert len(cases) == 5
    assert cases[0].category == "prompt-injection"


def test_safety_runner_passes_fake_provider() -> None:
    cases = load_safety_cases("data/redteam_dataset.jsonl")
    report = SafetyEvalRunner(FakeProvider()).run(cases)

    assert report.total == 5
    assert report.pass_rate == 1.0
    assert "secrets" in report.category_summary


def test_render_safety_markdown_report() -> None:
    cases = load_safety_cases("data/redteam_dataset.jsonl")
    payload = SafetyEvalRunner(FakeProvider()).run(cases).to_dict()

    markdown = render_safety_markdown_report(payload)

    assert "Safety Red-Team Report" in markdown
    assert "Category Summary" in markdown


def test_write_safety_report_bundle(tmp_path) -> None:
    cases = load_safety_cases("data/redteam_dataset.jsonl")
    payload = SafetyEvalRunner(FakeProvider()).run(cases).to_dict()

    json_path, markdown_path = write_safety_report_bundle(
        payload,
        report_dir=tmp_path,
        stem="redteam",
    )

    assert json.loads(json_path.read_text(encoding="utf-8"))["pass_rate"] == 1.0
    assert "Safety Red-Team Report" in markdown_path.read_text(encoding="utf-8")
