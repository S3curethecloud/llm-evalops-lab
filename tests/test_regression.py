from llm_lab.regression import gate_payload, tag_summary_from_results


def test_tag_summary_from_results_groups_by_tag() -> None:
    results = [
        {
            "passed": True,
            "tags": ["security", "secrets"],
            "metrics": {"token_f1": 1.0},
        },
        {
            "passed": False,
            "tags": ["security"],
            "metrics": {"token_f1": 0.5},
        },
    ]

    summary = tag_summary_from_results(results)

    assert summary["security"]["total"] == 2
    assert summary["security"]["passed"] == 1
    assert summary["security"]["pass_rate"] == 0.5
    assert summary["security"]["avg_token_f1"] == 0.75
    assert summary["secrets"]["pass_rate"] == 1.0


def test_gate_payload_fails_below_min_pass_rate() -> None:
    gate = gate_payload(
        {"pass_rate": 0.8},
        min_pass_rate=0.9,
    )

    assert not gate.passed
    assert gate.reasons


def test_gate_payload_fails_when_baseline_regresses() -> None:
    gate = gate_payload(
        {"pass_rate": 0.9},
        min_pass_rate=0.8,
        baseline={"pass_rate": 1.0},
        allowed_regression=0.05,
    )

    assert not gate.passed
    assert gate.pass_rate_delta == -0.09999999999999998


def test_gate_payload_passes_within_thresholds() -> None:
    gate = gate_payload(
        {"pass_rate": 0.98},
        min_pass_rate=0.95,
        baseline={"pass_rate": 1.0},
        allowed_regression=0.05,
    )

    assert gate.passed
    assert gate.pass_rate_delta == -0.020000000000000018
