from __future__ import annotations

from dataclasses import dataclass

from llm_lab.metrics import contains_all, exact_match, refusal_detected, token_f1
from llm_lab.prompts import DEFAULT_SYSTEM_PROMPT, PromptTemplate
from llm_lab.providers.base import LLMProvider
from llm_lab.safety import SafetyPolicy
from llm_lab.schemas import CaseResult, EvalCase, EvaluationReport


@dataclass(frozen=True)
class EvalThresholds:
    min_token_f1: float = 0.2


class EvalRunner:
    def __init__(
        self,
        provider: LLMProvider,
        *,
        prompt_template: PromptTemplate | None = None,
        safety_policy: SafetyPolicy | None = None,
        thresholds: EvalThresholds | None = None,
    ) -> None:
        self.provider = provider
        self.prompt_template = prompt_template or PromptTemplate()
        self.safety_policy = safety_policy or SafetyPolicy()
        self.thresholds = thresholds or EvalThresholds()

    def run(self, cases: list[EvalCase]) -> EvaluationReport:
        results = [self._run_case(case) for case in cases]
        total = len(results)
        passed = sum(1 for result in results if result.passed)
        avg_latency = sum(result.latency_ms for result in results) / total if total else 0.0
        return EvaluationReport(
            total=total,
            passed=passed,
            pass_rate=passed / total if total else 0.0,
            avg_latency_ms=avg_latency,
            results=results,
        )

    def _run_case(self, case: EvalCase) -> CaseResult:
        prompt = self.prompt_template.render(input=case.input)
        response = self.provider.generate(prompt, system_prompt=DEFAULT_SYSTEM_PROMPT)
        findings = self.safety_policy.inspect(response.text)

        metrics: dict[str, float | bool | str] = {
            "exact_match": exact_match(response.text, case.ideal),
            "contains_all": contains_all(response.text, case.must_include),
            "token_f1": token_f1(response.text, case.ideal),
            "refusal_detected": refusal_detected(response.text),
            "safety_findings": len(findings),
        }
        passed = bool(
            metrics["contains_all"]
            and not metrics["refusal_detected"]
            and metrics["token_f1"] >= self.thresholds.min_token_f1
            and metrics["safety_findings"] == 0
        )
        return CaseResult(
            case_id=case.id,
            input=case.input,
            ideal=case.ideal,
            output=response.text,
            passed=passed,
            metrics=metrics,
            tags=case.tags,
            latency_ms=response.latency_ms,
        )
