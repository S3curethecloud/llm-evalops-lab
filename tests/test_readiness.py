import json

from llm_lab.readiness import (
    build_readiness_payload,
    infer_gate_status,
    infer_report_type,
    render_readiness_markdown,
    write_readiness_bundle,
)


def _eval_report(pass_rate: float = 1.0, gate_passed: bool = True) -> dict:
    return {
        "metadata": {"schema_version": "evalops.report.v2"},
        "total": 3,
        "passed": 3,
        "pass_rate": pass_rate,
        "gate": {"passed": gate_passed},
    }


def _rag_report() -> dict:
    return {
        "total": 5,
        "passed": 5,
        "pass_rate": 1.0,
        "avg_recall_at_k": 1.0,
        "avg_groundedness": 1.0,
    }


def _redteam_report() -> dict:
    return {
        "metadata": {"schema_version": "redteam.report.v1"},
        "total": 5,
        "passed": 5,
        "pass_rate": 1.0,
        "category_summary": {},
    }


def test_infer_report_type() -> None:
    assert infer_report_type(_eval_report()) == "evalops"
    assert infer_report_type(_rag_report()) == "rag-evaluation"
    assert infer_report_type(_redteam_report()) == "safety-redteam"


def test_infer_gate_status() -> None:
    assert infer_gate_status(_eval_report(gate_passed=True)) is True
    assert infer_gate_status(_eval_report(gate_passed=False)) is False
    assert infer_gate_status(_rag_report()) is None


def test_build_readiness_payload_passes(tmp_path) -> None:
    eval_path = tmp_path / "eval.json"
    rag_path = tmp_path / "rag.json"
    redteam_path = tmp_path / "redteam.json"

    eval_path.write_text(json.dumps(_eval_report()), encoding="utf-8")
    rag_path.write_text(json.dumps(_rag_report()), encoding="utf-8")
    redteam_path.write_text(json.dumps(_redteam_report()), encoding="utf-8")

    payload = build_readiness_payload([eval_path, rag_path, redteam_path])

    assert payload["release_ready"] is True
    assert payload["passed"] == 3


def test_build_readiness_payload_fails_failed_gate(tmp_path) -> None:
    report_path = tmp_path / "eval.json"
    report_path.write_text(json.dumps(_eval_report(gate_passed=False)), encoding="utf-8")

    payload = build_readiness_payload([report_path])

    assert payload["release_ready"] is False
    assert payload["checks"][0]["passed"] is False


def test_write_readiness_bundle(tmp_path) -> None:
    report_path = tmp_path / "eval.json"
    report_path.write_text(json.dumps(_eval_report()), encoding="utf-8")
    payload = build_readiness_payload([report_path])

    json_path, markdown_path = write_readiness_bundle(
        payload,
        report_dir=tmp_path / "reports",
        stem="readiness",
    )

    assert json.loads(json_path.read_text(encoding="utf-8"))["release_ready"] is True
    assert "Release Readiness Dashboard" in markdown_path.read_text(encoding="utf-8")


def test_render_readiness_markdown() -> None:
    payload = {
        "metadata": {"min_pass_rate": 1.0},
        "total": 1,
        "passed": 1,
        "pass_rate": 1.0,
        "release_ready": True,
        "checks": [
            {
                "name": "eval",
                "report_type": "evalops",
                "pass_rate": 1.0,
                "gate_passed": True,
                "passed": True,
                "reason": "ready",
            }
        ],
    }

    markdown = render_readiness_markdown(payload)

    assert "Release Readiness Dashboard" in markdown
    assert "READY" in markdown
