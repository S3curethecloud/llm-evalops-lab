from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    alias: str
    model: str
    description: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "alias": self.alias,
            "model": self.model,
            "description": self.description,
        }


@dataclass(frozen=True)
class ModelSelection:
    provider: str
    model: str
    alias: str | None
    source: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "provider": self.provider,
            "model": self.model,
            "alias": self.alias,
            "source": self.source,
        }


DEFAULT_MODELS: tuple[ModelSpec, ...] = (
    ModelSpec(
        provider="fake",
        alias="default",
        model="fake-deterministic-v1",
        description="Deterministic fake provider model for local tests and CI.",
    ),
    ModelSpec(
        provider="fake",
        alias="ci",
        model="fake-deterministic-v1",
        description="CI-safe deterministic fake model alias.",
    ),
    ModelSpec(
        provider="openai",
        alias="default",
        model="gpt-4o-mini",
        description="Default OpenAI smoke/eval model.",
    ),
    ModelSpec(
        provider="openai",
        alias="smoke",
        model="gpt-4o-mini",
        description="OpenAI smoke-test model alias.",
    ),
)


def load_model_registry(path: str | Path | None = None) -> list[ModelSpec]:
    if path is None:
        default_path = Path("config/model_registry.json")
        if default_path.exists():
            return _load_registry_file(default_path)
        return list(DEFAULT_MODELS)

    return _load_registry_file(Path(path))


def resolve_model(
    provider: str,
    *,
    model: str | None = None,
    model_alias: str | None = None,
    registry_path: str | Path | None = None,
) -> ModelSelection:
    if model:
        return ModelSelection(
            provider=provider,
            model=model,
            alias=model_alias,
            source="explicit",
        )

    alias = model_alias or "default"
    registry = load_model_registry(registry_path)

    for spec in registry:
        if spec.provider == provider and spec.alias == alias:
            return ModelSelection(
                provider=provider,
                model=spec.model,
                alias=spec.alias,
                source="registry",
            )

    available = sorted(
        f"{spec.provider}:{spec.alias}" for spec in registry if spec.provider == provider
    )
    available_text = ", ".join(available) if available else "none"
    raise ValueError(
        f"No model alias '{alias}' found for provider '{provider}'. "
        f"Available aliases: {available_text}"
    )


def render_model_registry_markdown(models: Sequence[ModelSpec]) -> str:
    lines = [
        "# Model Registry",
        "",
        "| Provider | Alias | Model | Description |",
        "| --- | --- | --- | --- |",
    ]

    for spec in models:
        lines.append(
            f"| {_safe_cell(spec.provider)} | {_safe_cell(spec.alias)} | "
            f"{_safe_cell(spec.model)} | {_safe_cell(spec.description)} |"
        )

    return "\n".join(lines) + "\n"


def render_model_registry_json(models: Sequence[ModelSpec]) -> str:
    return json.dumps(
        {"models": [model.to_dict() for model in models]},
        indent=2,
        sort_keys=True,
    )


def _load_registry_file(path: Path) -> list[ModelSpec]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    items = raw.get("models", raw) if isinstance(raw, Mapping) else raw

    if not isinstance(items, list):
        raise ValueError("Model registry must be a list or an object with a 'models' list.")

    return [_model_spec_from_mapping(item) for item in items]


def _model_spec_from_mapping(item: Any) -> ModelSpec:
    if not isinstance(item, Mapping):
        raise ValueError("Each model registry entry must be an object.")

    return ModelSpec(
        provider=str(item["provider"]),
        alias=str(item["alias"]),
        model=str(item["model"]),
        description=str(item.get("description", "")),
    )


def _safe_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
