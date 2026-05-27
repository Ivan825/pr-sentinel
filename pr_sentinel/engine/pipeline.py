from pr_sentinel.core.models import AnalysisResult, PullRequestInfo
from pr_sentinel.rules.base import RuleContext
from pr_sentinel.rules.default_rules import build_default_rule_registry
from pr_sentinel.rules.registry import RuleRegistry


class AnalysisPipeline:
    def __init__(self, rule_registry: RuleRegistry | None = None) -> None:
        self.rule_registry = rule_registry or build_default_rule_registry()

    def analyze(self, pull_request: PullRequestInfo) -> AnalysisResult:
        context = RuleContext(
            pull_request=pull_request,
            changed_files=pull_request.changed_files,
        )

        findings = self.rule_registry.evaluate_all(context)

        return AnalysisResult(
            pr=pull_request,
            findings=findings,
            test_recommendations=[],
            risk_score=None,
            summary=None,
        )