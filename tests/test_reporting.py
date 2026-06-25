import json

from llm_lab.dataset import load_jsonl
from llm_lab.evals import EvalRunner
from llm_lab.providers.fake import FakeProvider
from llm_lab.reporting import render_markdown_report, report_payload, write_report_bundle


def test_report_payload_includes_metadata() -> None:
    cases = load_jsonl("data/sample_dataset.jsonl")
    report = EvalRunner(FakeProvider()).run(cases)

    payload = report_payload(
        report,
        dataset="data/sample_dataset.jsonl",
        provider="fake",
    )

    assert payload["metadata"]["schema_version"] == "evalops.report.v2"
    assert payload["metadata"]["provider"] == "fake"
    assert payload["pass_rate"] == 1.0
    assert "tag_summary" in payload


def test_render_markdown_report_contains_summary() -> None:
    cases = load_jsonl("data/sample_dataset.jsonl")
    report = EvalRunner(FakeProvider()).run(cases)
    payload = report_payload(report, dataset="sample", provider="fake")

    markdown = render_markdown_report(payload)

    assert "# LLM EvalOps Evaluation Report" in markdown
    assert "Pass rate" in markdown
    assert "case-rag-001" in markdown


def test_write_report_bundle_creates_json_and_markdown(tmp_path) -> None:
    cases = load_jsonl("data/sample_dataset.jsonl")
    report = EvalRunner(FakeProvider()).run(cases)

    json_path, markdown_path = write_report_bundle(
        report,
        report_dir=tmp_path,
        dataset="data/sample_dataset.jsonl",
        provider="fake",
        stem="sample",
    )

    assert json_path.exists()
    assert markdown_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["total"] == 3
    assert markdown_path.read_text(encoding="utf-8").startswith("# LLM EvalOps Evaluation Report")
