import json

import pytest

from llm_lab.model_registry import (
    load_model_registry,
    render_model_registry_json,
    render_model_registry_markdown,
    resolve_model,
)


def test_resolve_default_fake_model() -> None:
    selection = resolve_model("fake")

    assert selection.provider == "fake"
    assert selection.model == "fake-deterministic-v1"
    assert selection.alias == "default"
    assert selection.source == "registry"


def test_explicit_model_overrides_alias() -> None:
    selection = resolve_model("openai", model="gpt-test-model", model_alias="smoke")

    assert selection.provider == "openai"
    assert selection.model == "gpt-test-model"
    assert selection.alias == "smoke"
    assert selection.source == "explicit"


def test_custom_registry_file(tmp_path) -> None:
    registry_path = tmp_path / "models.json"
    registry_path.write_text(
        json.dumps(
            {
                "models": [
                    {
                        "provider": "fake",
                        "alias": "custom",
                        "model": "fake-custom-v1",
                        "description": "Custom fake model.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    selection = resolve_model("fake", model_alias="custom", registry_path=registry_path)

    assert selection.model == "fake-custom-v1"


def test_unknown_alias_lists_available_aliases() -> None:
    with pytest.raises(ValueError, match="Available aliases"):
        resolve_model("fake", model_alias="missing")


def test_render_model_registry_outputs() -> None:
    models = load_model_registry()

    markdown = render_model_registry_markdown(models)
    raw_json = render_model_registry_json(models)

    assert "Model Registry" in markdown
    assert "fake-deterministic-v1" in markdown
    assert "gpt-4o-mini" in raw_json
