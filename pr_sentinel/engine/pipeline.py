from pr_sentinel.core.models import AnalysisResult, PullRequestInfo
from pr_sentinel.risk.scorer import RiskScorer
from pr_sentinel.rules.base import RuleContext
from pr_sentinel.rules.default_rules import build_default_rule_registry
from pr_sentinel.rules.registry import RuleRegistry


class AnalysisPipeline:
    def __init__(
        self,
        rule_registry: RuleRegistry | None = None,
        risk_scorer: RiskScorer | None = None,
    ) -> None:
        self.rule_registry = rule_registry or build_default_rule_registry()
        self.risk_scorer = risk_scorer or RiskScorer()

    def analyze(self, pull_request: PullRequestInfo) -> AnalysisResult:
        context = RuleContext(
            pull_request=pull_request,
            changed_files=pull_request.changed_files,
        )

        findings = self.rule_registry.evaluate_all(context)
        risk_score = self.risk_scorer.score_findings(findings)

        return AnalysisResult(
            pr=pull_request,
            findings=findings,
            test_recommendations=[],
            risk_score=risk_score,
            summary=None,
        )