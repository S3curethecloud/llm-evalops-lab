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
from llm_lab.rag.eval import RAGEvaluator, load_rag_eval_cases, write_rag_report_bundle
from llm_lab.rag.index import TokenIndex
from llm_lab.regression import gate_payload, load_report
from llm_lab.reporting import (
    report_payload,
    write_json_report,
    write_markdown_report,
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
    eval_parser.add_argument("--min-pass-rate", type=float, default=1.0)
    eval_parser.add_argument("--baseline-report", default=None)
    eval_parser.add_argument("--allowed-regression", type=float, default=0.0)

    retrieve_parser = subparsers.add_parser("retrieve", help="Run local retrieval over text files")
    retrieve_parser.add_argument("--query", required=True)
    retrieve_parser.add_argument("--docs", nargs="+", required=True)
    retrieve_parser.add_argument("--top-k", type=int, default=3)

    rag_eval_parser = subparsers.add_parser("rag-eval", help="Run a retrieval evaluation dataset")
    rag_eval_parser.add_argument("--dataset", required=True)
    rag_eval_parser.add_argument("--docs", nargs="+", required=True)
    rag_eval_parser.add_argument("--top-k", type=int, default=3)
    rag_eval_parser.add_argument("--min-pass-rate", type=float, default=1.0)
    rag_eval_parser.add_argument("--min-recall-at-k", type=float, default=1.0)
    rag_eval_parser.add_argument("--min-groundedness", type=float, default=1.0)
    rag_eval_parser.add_argument("--report-dir", default=None)
    rag_eval_parser.add_argument("--report-stem", default="rag-eval-report")

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

        baseline = load_report(Path(args.baseline_report)) if args.baseline_report else None
        gate = gate_payload(
            payload,
            min_pass_rate=args.min_pass_rate,
            baseline=baseline,
            allowed_regression=args.allowed_regression,
        )
        payload["gate"] = gate.to_dict()

        rendered = json.dumps(payload, indent=2, sort_keys=True)
        print(rendered)

        if args.output:
            write_json_report(payload, Path(args.output))

        if args.markdown_output:
            write_markdown_report(payload, Path(args.markdown_output))

        if args.report_dir:
            report_dir = Path(args.report_dir)
            json_path = report_dir / f"{args.report_stem}.json"
            markdown_path = report_dir / f"{args.report_stem}.md"
            write_json_report(payload, json_path)
            write_markdown_report(payload, markdown_path)
            print(f"Wrote JSON report: {json_path}", file=sys.stderr)
            print(f"Wrote Markdown report: {markdown_path}", file=sys.stderr)

        return 0 if gate.passed else 1

    if args.command == "rag-eval":
        index = TokenIndex.from_paths(args.docs)
        cases = load_rag_eval_cases(args.dataset)
        report = RAGEvaluator(
            index,
            top_k=args.top_k,
            min_recall_at_k=args.min_recall_at_k,
            min_groundedness=args.min_groundedness,
        ).run(cases)
        payload = report.to_dict()
        rendered = json.dumps(payload, indent=2, sort_keys=True)
        print(rendered)

        if args.report_dir:
            json_path, markdown_path = write_rag_report_bundle(
                payload,
                report_dir=Path(args.report_dir),
                stem=args.report_stem,
            )
            print(f"Wrote RAG JSON report: {json_path}", file=sys.stderr)
            print(f"Wrote RAG Markdown report: {markdown_path}", file=sys.stderr)

        return 0 if report.pass_rate >= args.min_pass_rate else 1

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
