.PHONY: install test lint format check eval

install:
	python -m pip install --upgrade pip
	python -m pip install -e '.[dev]'

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

check:
	ruff check .
	ruff format --check .
	pytest

eval:
	llm-lab eval --dataset data/sample_dataset.jsonl --provider fake
