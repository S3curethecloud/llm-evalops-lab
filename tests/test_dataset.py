from pathlib import Path

import pytest

from llm_lab.dataset import DatasetError, load_jsonl


def test_load_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        '{"id":"a","input":"hello","ideal":"world","tags":["x"],"must_include":["w"]}\n',
        encoding="utf-8",
    )
    cases = load_jsonl(path)
    assert cases[0].id == "a"
    assert cases[0].must_include == ["w"]


def test_load_jsonl_rejects_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"id":"a"}\n', encoding="utf-8")
    with pytest.raises(DatasetError):
        load_jsonl(path)
