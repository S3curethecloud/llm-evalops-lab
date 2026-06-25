import json

from llm_lab.dashboard import (
    build_dashboard_payload,
    dashboard_report_from_path,
    infer_dashboard_report_type,
    render_dashboard_html,
    write_dashboard_bundle,
)


def _eval_report() -> dict:
    return {
        "metadata": {"schema_version": "evalops.report.v2"},
        "total": 3,
        "passed": 3,
        "pass_rate": 1.0,
        "gate": {"passed": True},
    }


def _rag_report() -> dict:
    return {
        "total": 5,
        "passed": 5,
        "pass_rate": 1.0,
        "avg_recall_at_k": 1.0,
        "avg_groundedness": 1.0,
    }


def _readiness_report() -> dict:
    return {
        "metadata": {"schema_version": "release-readiness.report.v1"},
        "total": 4,
        "passed": 4,
        "pass_rate": 1.0,
        "release_ready": True,
    }


def test_infer_dashboard_report_type() -> None:
    assert infer_dashboard_report_type(_eval_report()) == "evalops"
    assert infer_dashboard_report_type(_rag_report()) == "rag-evaluation"
    assert infer_dashboard_report_type(_readiness_report()) == "release-readiness"


def test_dashboard_report_from_path(tmp_path) -> None:
    report_path = tmp_path / "eval.json"
    report_path.write_text(json.dumps(_eval_report()), encoding="utf-8")

    report = dashboard_report_from_path(report_path)

    assert report.name == "eval"
    assert report.pass_rate == 1.0
    assert report.gate_passed is True


def test_build_dashboard_payload_ready(tmp_path) -> None:
    eval_path = tmp_path / "eval.json"
    rag_path = tmp_path / "rag.json"
    readiness_path = tmp_path / "readiness.json"

    eval_path.write_text(json.dumps(_eval_report()), encoding="utf-8")
    rag_path.write_text(json.dumps(_rag_report()), encoding="utf-8")
    readiness_path.write_text(json.dumps(_readiness_report()), encoding="utf-8")

    payload = build_dashboard_payload([eval_path, rag_path, readiness_path])

    assert payload["release_ready"] is True
    assert payload["summary"]["evalops_reports"] == 1
    assert payload["summary"]["rag_reports"] == 1
    assert payload["summary"]["readiness_reports"] == 1


def test_render_dashboard_html() -> None:
    payload = {
        "metadata": {"generated_at_utc": "2026-01-01T00:00:00+00:00"},
        "release_ready": True,
        "summary": {
            "evalops_reports": 1,
            "rag_reports": 1,
            "safety_reports": 1,
            "readiness_reports": 1,
        },
        "reports": [
            {
                "name": "eval",
                "report_type": "evalops",
                "path": "reports/eval.json",
                "pass_rate": 1.0,
                "passed": 3,
                "total": 3,
                "gate_passed": True,
            }
        ],
    }

    html = render_dashboard_html(payload)

    assert "LLM EvalOps Lab Dashboard" in html
    assert "Status: READY" in html
    assert "reports/eval.json" in html


def test_write_dashboard_bundle(tmp_path) -> None:
    payload = {
        "metadata": {"generated_at_utc": "2026-01-01T00:00:00+00:00"},
        "release_ready": True,
        "summary": {
            "evalops_reports": 1,
            "rag_reports": 0,
            "safety_reports": 0,
            "readiness_reports": 0,
        },
        "reports": [],
    }

    json_path, html_path = write_dashboard_bundle(
        payload,
        report_dir=tmp_path,
        stem="dashboard",
    )

    assert json.loads(json_path.read_text(encoding="utf-8"))["release_ready"] is True
    assert "Release Evidence Dashboard" in html_path.read_text(encoding="utf-8")
