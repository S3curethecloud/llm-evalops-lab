import json

from llm_lab.experiments import (
    append_experiment_record,
    experiment_record_from_payload,
    make_run_id,
    render_scoreboard_markdown,
    write_scoreboards,
)


def _payload() -> dict:
    return {
        "metadata": {
            "run_id": "eval-test-run",
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
            "provider": "fake",
            "model": "fake-deterministic-v1",
            "dataset": "data/sample_dataset.jsonl",
        },
        "total": 3,
        "passed": 3,
        "pass_rate": 1.0,
        "avg_latency_ms": 0.1,
        "gate": {"passed": True},
    }


def test_make_run_id_has_prefix() -> None:
    assert make_run_id("eval").startswith("eval-")


def test_experiment_record_from_payload() -> None:
    record = experiment_record_from_payload(_payload(), report_path="reports/sample.json")

    assert record.run_id == "eval-test-run"
    assert record.provider == "fake"
    assert record.model == "fake-deterministic-v1"
    assert record.pass_rate == 1.0
    assert record.gate_passed is True


def test_append_experiment_record(tmp_path) -> None:
    registry = tmp_path / "registry.jsonl"

    record = append_experiment_record(
        _payload(),
        registry,
        report_path="reports/sample.json",
    )

    lines = registry.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["run_id"] == record.run_id


def test_write_scoreboards(tmp_path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_payload()), encoding="utf-8")

    csv_path, markdown_path = write_scoreboards(
        [report_path],
        csv_path=tmp_path / "scoreboard.csv",
        markdown_path=tmp_path / "scoreboard.md",
    )

    assert csv_path.exists()
    assert markdown_path.exists()
    assert "fake-deterministic-v1" in csv_path.read_text(encoding="utf-8")
    assert "Model Comparison Scoreboard" in markdown_path.read_text(encoding="utf-8")


def test_render_scoreboard_markdown() -> None:
    record = experiment_record_from_payload(_payload(), report_path="reports/sample.json")
    markdown = render_scoreboard_markdown([record])

    assert "Model Comparison Scoreboard" in markdown
    assert "eval-test-run" in markdown
