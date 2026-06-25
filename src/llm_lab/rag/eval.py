from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm_lab.rag.index import TokenIndex


@dataclass(frozen=True)
class RAGEvalCase:
    id: str
    query: str
    expected_doc_ids: list[str]
    expected_terms: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RAGCaseResult:
    case_id: str
    query: str
    expected_doc_ids: list[str]
    retrieved_doc_ids: list[str]
    matched_doc_ids: list[str]
    recall_at_k: float
    context_precision: float
    grounded_terms_found: list[str]
    groundedness: float
    passed: bool
    tags: list[str]


@dataclass(frozen=True)
class RAGEvaluationReport:
    total: int
    passed: int
    pass_rate: float
    avg_recall_at_k: float
    avg_context_precision: float
    avg_groundedness: float
    results: list[RAGCaseResult]
    tag_summary: dict[str, dict[str, float | int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "pass_rate": self.pass_rate,
            "avg_recall_at_k": self.avg_recall_at_k,
            "avg_context_precision": self.avg_context_precision,
            "avg_groundedness": self.avg_groundedness,
            "tag_summary": self.tag_summary,
            "results": [
                {
                    "case_id": item.case_id,
                    "query": item.query,
                    "expected_doc_ids": item.expected_doc_ids,
                    "retrieved_doc_ids": item.retrieved_doc_ids,
                    "matched_doc_ids": item.matched_doc_ids,
                    "recall_at_k": item.recall_at_k,
                    "context_precision": item.context_precision,
                    "grounded_terms_found": item.grounded_terms_found,
                    "groundedness": item.groundedness,
                    "passed": item.passed,
                    "tags": item.tags,
                }
                for item in self.results
            ],
        }


def load_rag_eval_cases(path: str | Path) -> list[RAGEvalCase]:
    cases: list[RAGEvalCase] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        raw = json.loads(line)
        cases.append(
            RAGEvalCase(
                id=str(raw["id"]),
                query=str(raw["query"]),
                expected_doc_ids=[str(item) for item in raw["expected_doc_ids"]],
                expected_terms=[str(item) for item in raw.get("expected_terms", [])],
                tags=[str(item) for item in raw.get("tags", [])],
            )
        )

    return cases


class RAGEvaluator:
    def __init__(
        self,
        index: TokenIndex,
        *,
        top_k: int = 3,
        min_recall_at_k: float = 1.0,
        min_groundedness: float = 1.0,
    ) -> None:
        self.index = index
        self.top_k = top_k
        self.min_recall_at_k = min_recall_at_k
        self.min_groundedness = min_groundedness

    def run(self, cases: Sequence[RAGEvalCase]) -> RAGEvaluationReport:
        results = [self._run_case(case) for case in cases]
        total = len(results)
        passed = sum(1 for result in results if result.passed)

        return RAGEvaluationReport(
            total=total,
            passed=passed,
            pass_rate=passed / total if total else 0.0,
            avg_recall_at_k=_average(item.recall_at_k for item in results),
            avg_context_precision=_average(item.context_precision for item in results),
            avg_groundedness=_average(item.groundedness for item in results),
            results=results,
            tag_summary=rag_tag_summary(results),
        )

    def _run_case(self, case: RAGEvalCase) -> RAGCaseResult:
        results = self.index.search(case.query, top_k=self.top_k)
        retrieved_doc_ids = [item.document.id for item in results]
        matched_doc_ids = [
            doc_id for doc_id in retrieved_doc_ids if doc_id in set(case.expected_doc_ids)
        ]

        recall_at_k = retrieval_recall_at_k(
            retrieved_doc_ids,
            expected_doc_ids=case.expected_doc_ids,
        )
        context_precision = retrieval_context_precision(
            retrieved_doc_ids,
            expected_doc_ids=case.expected_doc_ids,
        )

        context_text = "\n".join(item.document.text for item in results)
        grounded_terms_found = grounded_terms(context_text, case.expected_terms)
        groundedness = (
            len(grounded_terms_found) / len(case.expected_terms) if case.expected_terms else 1.0
        )

        passed = recall_at_k >= self.min_recall_at_k and groundedness >= self.min_groundedness

        return RAGCaseResult(
            case_id=case.id,
            query=case.query,
            expected_doc_ids=case.expected_doc_ids,
            retrieved_doc_ids=retrieved_doc_ids,
            matched_doc_ids=matched_doc_ids,
            recall_at_k=recall_at_k,
            context_precision=context_precision,
            grounded_terms_found=grounded_terms_found,
            groundedness=groundedness,
            passed=passed,
            tags=case.tags,
        )


def retrieval_recall_at_k(
    retrieved_doc_ids: Sequence[str],
    *,
    expected_doc_ids: Sequence[str],
) -> float:
    expected = set(expected_doc_ids)
    if not expected:
        return 1.0
    retrieved = set(retrieved_doc_ids)
    return len(expected & retrieved) / len(expected)


def retrieval_context_precision(
    retrieved_doc_ids: Sequence[str],
    *,
    expected_doc_ids: Sequence[str],
) -> float:
    if not retrieved_doc_ids:
        return 0.0
    expected = set(expected_doc_ids)
    return sum(1 for doc_id in retrieved_doc_ids if doc_id in expected) / len(retrieved_doc_ids)


def grounded_terms(context: str, expected_terms: Sequence[str]) -> list[str]:
    lowered = context.lower()
    return [term for term in expected_terms if term.lower() in lowered]


def rag_tag_summary(results: Sequence[RAGCaseResult]) -> dict[str, dict[str, float | int]]:
    buckets: dict[str, dict[str, float | int]] = {}

    for result in results:
        for tag in result.tags:
            bucket = buckets.setdefault(
                tag,
                {
                    "total": 0,
                    "passed": 0,
                    "pass_rate": 0.0,
                    "avg_recall_at_k": 0.0,
                    "avg_context_precision": 0.0,
                    "avg_groundedness": 0.0,
                },
            )
            bucket["total"] = int(bucket["total"]) + 1
            bucket["passed"] = int(bucket["passed"]) + int(result.passed)
            bucket["avg_recall_at_k"] = float(bucket["avg_recall_at_k"]) + result.recall_at_k
            bucket["avg_context_precision"] = (
                float(bucket["avg_context_precision"]) + result.context_precision
            )
            bucket["avg_groundedness"] = float(bucket["avg_groundedness"]) + result.groundedness

    for bucket in buckets.values():
        total = int(bucket["total"])
        passed = int(bucket["passed"])
        bucket["pass_rate"] = passed / total if total else 0.0
        bucket["avg_recall_at_k"] = float(bucket["avg_recall_at_k"]) / total if total else 0.0
        bucket["avg_context_precision"] = (
            float(bucket["avg_context_precision"]) / total if total else 0.0
        )
        bucket["avg_groundedness"] = float(bucket["avg_groundedness"]) / total if total else 0.0

    return dict(sorted(buckets.items()))


def render_rag_markdown_report(payload: Mapping[str, Any]) -> str:
    lines = [
        "# RAG Evaluation Report",
        "",
        "## Summary",
        "",
        f"- Total cases: `{int(payload.get('total', 0))}`",
        f"- Passed cases: `{int(payload.get('passed', 0))}`",
        f"- Pass rate: `{float(payload.get('pass_rate', 0.0)):.3f}`",
        f"- Average recall@k: `{float(payload.get('avg_recall_at_k', 0.0)):.3f}`",
        f"- Average context precision: `{float(payload.get('avg_context_precision', 0.0)):.3f}`",
        f"- Average groundedness: `{float(payload.get('avg_groundedness', 0.0)):.3f}`",
        "",
        "## Tag Summary",
        "",
        "| Tag | Total | Passed | Pass Rate | Recall@k | Context Precision | Groundedness |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    tag_summary = payload.get("tag_summary", {})
    if isinstance(tag_summary, Mapping):
        for tag, summary in tag_summary.items():
            if not isinstance(summary, Mapping):
                continue
            lines.append(
                (
                    "| {tag} | {total} | {passed} | {pass_rate:.3f} | "
                    "{recall:.3f} | {precision:.3f} | {groundedness:.3f} |"
                ).format(
                    tag=_safe_cell(tag),
                    total=int(summary.get("total", 0)),
                    passed=int(summary.get("passed", 0)),
                    pass_rate=float(summary.get("pass_rate", 0.0)),
                    recall=float(summary.get("avg_recall_at_k", 0.0)),
                    precision=float(summary.get("avg_context_precision", 0.0)),
                    groundedness=float(summary.get("avg_groundedness", 0.0)),
                )
            )

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case | Passed | Recall@k | Context Precision | Groundedness | Retrieved Docs |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )

    results = payload.get("results", [])
    if isinstance(results, list):
        for item in results:
            if not isinstance(item, Mapping):
                continue
            retrieved_doc_ids = item.get("retrieved_doc_ids", [])
            retrieved = (
                ", ".join(str(doc_id) for doc_id in retrieved_doc_ids)
                if isinstance(retrieved_doc_ids, list)
                else ""
            )
            lines.append(
                (
                    "| {case_id} | {passed} | {recall:.3f} | {precision:.3f} | "
                    "{groundedness:.3f} | {retrieved} |"
                ).format(
                    case_id=_safe_cell(item.get("case_id", "")),
                    passed="yes" if bool(item.get("passed")) else "no",
                    recall=float(item.get("recall_at_k", 0.0)),
                    precision=float(item.get("context_precision", 0.0)),
                    groundedness=float(item.get("groundedness", 0.0)),
                    retrieved=_safe_cell(retrieved),
                )
            )

    return "\n".join(lines) + "\n"


def write_rag_report_bundle(
    payload: Mapping[str, Any],
    *,
    report_dir: Path,
    stem: str,
) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{stem}.json"
    markdown_path = report_dir / f"{stem}.md"

    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_rag_markdown_report(payload), encoding="utf-8")

    return json_path, markdown_path


def _average(values: Iterable[float]) -> float:
    materialized = list(values)
    return sum(materialized) / len(materialized) if materialized else 0.0


def _safe_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
