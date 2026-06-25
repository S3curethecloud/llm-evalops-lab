from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from llm_lab.dataset import load_jsonl
from llm_lab.evals import EvalRunner
from llm_lab.providers.base import LLMProvider
from llm_lab.providers.fake import FakeProvider
from llm_lab.providers.openai_provider import OpenAIProvider
from llm_lab.rag.index import TokenIndex
from llm_lab.reporting import (
    report_payload,
    write_json_report,
    write_markdown_report,
    write_report_bundle,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="llm-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser("ask", help="Generate one model response")
    ask_parser.add_argument("--provider", choices=["fake", "openai"], default="fake")
    ask_parser.add_argument("--input", required=True)

    eval_parser = subparsers.add_parser("eval", help="Run an evaluation dataset")
    eval_parser.add_argument("--dataset", required=True)
    eval_parser.add_argument("--provider", choices=["fake", "openai"], default="fake")
    eval_parser.add_argument("--output", default=None)
    eval_parser.add_argument("--markdown-output", default=None)
    eval_parser.add_argument("--report-dir", default=None)
    eval_parser.add_argument("--report-stem", default="eval-report")

    retrieve_parser = subparsers.add_parser("retrieve", help="Run local retrieval over text files")
    retrieve_parser.add_argument("--query", required=True)
    retrieve_parser.add_argument("--docs", nargs="+", required=True)
    retrieve_parser.add_argument("--top-k", type=int, default=3)

    args = parser.parse_args(argv)

    if args.command == "ask":
        provider = _provider(args.provider)
        response = provider.generate(args.input)
        print(response.text)
        return 0

    if args.command == "eval":
        provider = _provider(args.provider)
        cases = load_jsonl(args.dataset)
        report = EvalRunner(provider).run(cases)
        payload = report_payload(report, dataset=args.dataset, provider=args.provider)
        rendered = json.dumps(payload, indent=2, sort_keys=True)
        print(rendered)

        if args.output:
            write_json_report(payload, Path(args.output))

        if args.markdown_output:
            write_markdown_report(payload, Path(args.markdown_output))

        if args.report_dir:
            json_path, markdown_path = write_report_bundle(
                report,
                report_dir=Path(args.report_dir),
                dataset=args.dataset,
                provider=args.provider,
                stem=args.report_stem,
            )
            print(f"Wrote JSON report: {json_path}", file=sys.stderr)
            print(f"Wrote Markdown report: {markdown_path}", file=sys.stderr)

        return 0 if report.pass_rate == 1.0 else 1

    if args.command == "retrieve":
        index = TokenIndex.from_paths(args.docs)
        results = index.search(args.query, top_k=args.top_k)
        print(
            json.dumps(
                [
                    {
                        "id": item.document.id,
                        "score": item.score,
                        "metadata": item.document.metadata,
                    }
                    for item in results
                ],
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _provider(name: str) -> LLMProvider:
    if name == "fake":
        return FakeProvider()
    if name == "openai":
        return OpenAIProvider()
    raise ValueError(f"Unsupported provider: {name}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
