from llm_lab.cli import main


def test_cli_models_markdown(capsys) -> None:
    exit_code = main(["models"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Model Registry" in captured.out
    assert "fake-deterministic-v1" in captured.out


def test_cli_ask_model_alias(capsys) -> None:
    exit_code = main(
        [
            "ask",
            "--provider",
            "fake",
            "--model-alias",
            "ci",
            "--input",
            "Define RAG in one sentence.",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Retrieval augmented generation" in captured.out
