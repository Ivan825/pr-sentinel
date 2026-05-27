from pr_sentinel.core.models import AnalysisResult, PullRequestInfo
from pr_sentinel.llm.semantic_reviewer import SemanticReviewer
from pr_sentinel.risk.scorer import RiskScorer
from pr_sentinel.rules.base import RuleContext
from pr_sentinel.rules.default_rules import build_default_rule_registry
from pr_sentinel.rules.registry import RuleRegistry
from pr_sentinel.testsuggester.mapper import TestRecommendationMapper


class AnalysisPipeline:
    def __init__(
        self,
        rule_registry: RuleRegistry | None = None,
        risk_scorer: RiskScorer | None = None,
        test_mapper: TestRecommendationMapper | None = None,
        semantic_reviewer: SemanticReviewer | None = None,
        use_llm: bool = False,
    ) -> None:
        self.rule_registry = rule_registry or build_default_rule_registry()
        self.risk_scorer = risk_scorer or RiskScorer()
        self.test_mapper = test_mapper or TestRecommendationMapper()
        self.semantic_reviewer = semantic_reviewer or SemanticReviewer()
        self.use_llm = use_llm

    def analyze(self, pull_request: PullRequestInfo) -> AnalysisResult:
        context = RuleContext(
            pull_request=pull_request,
            changed_files=pull_request.changed_files,
        )

        deterministic_findings = self.rule_registry.evaluate_all(context)
        test_recommendations = self.test_mapper.recommend_for_changed_files(
            pull_request.changed_files
        )
        deterministic_risk_score = self.risk_scorer.score_findings(deterministic_findings)

        result = AnalysisResult(
            pr=pull_request,
            findings=deterministic_findings,
            test_recommendations=test_recommendations,
            risk_score=deterministic_risk_score,
            summary=None,
        )

        if not self.use_llm:
            return result

        llm_review = self.semantic_reviewer.review(result)
        ai_findings = self.semantic_reviewer.to_core_findings(llm_review)
        all_findings = [*deterministic_findings, *ai_findings]

        final_risk_score = self.risk_scorer.score_findings(
            all_findings,
            ai_adjustment=llm_review.ai_adjustment,
            ai_adjustment_reasons=llm_review.ai_adjustment_reasons,
        )

        return AnalysisResult(
            pr=pull_request,
            findings=all_findings,
            test_recommendations=test_recommendations,
            risk_score=final_risk_score,
            summary=None,
        )