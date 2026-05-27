from collections import defaultdict

from pr_sentinel.core.enums import FindingCategory, RiskBand
from pr_sentinel.core.models import Finding, RiskScore
from pr_sentinel.risk.weights import (
    CATEGORY_MULTIPLIERS,
    HIGH_RISK_RULE_BONUSES,
    MAX_CATEGORY_CONTRIBUTION,
    SEVERITY_WEIGHTS,
)


def determine_risk_band(score: int) -> RiskBand:
    if score >= 80:
        return RiskBand.CRITICAL

    if score >= 60:
        return RiskBand.HIGH

    if score >= 30:
        return RiskBand.MEDIUM

    return RiskBand.LOW


class RiskScorer:
    def score_findings(
        self,
        findings: list[Finding],
        ai_adjustment: int = 0,
        ai_adjustment_reasons: list[str] | None = None,
    ) -> RiskScore:
        raw_breakdown: dict[str, int] = defaultdict(int)

        for finding in findings:
            category = finding.category
            category_key = category.value

            base = SEVERITY_WEIGHTS[finding.severity]
            multiplier = CATEGORY_MULTIPLIERS.get(category, 1.0)
            confidence_adjusted = base * multiplier * finding.confidence
            rule_bonus = HIGH_RISK_RULE_BONUSES.get(finding.rule_id, 0)

            contribution = round(confidence_adjusted + rule_bonus)
            raw_breakdown[category_key] += max(contribution, 0)

        capped_breakdown = self._cap_category_breakdown(dict(raw_breakdown))
        deterministic_score = min(sum(capped_breakdown.values()), 100)

        bounded_ai_adjustment = self._bound_ai_adjustment(ai_adjustment)
        final_score = min(max(deterministic_score + bounded_ai_adjustment, 0), 100)

        return RiskScore(
            score=final_score,
            band=determine_risk_band(final_score),
            breakdown=capped_breakdown,
            deterministic_score=deterministic_score,
            ai_adjustment=bounded_ai_adjustment,
            ai_adjustment_reasons=ai_adjustment_reasons or [],
        )

    def _cap_category_breakdown(self, breakdown: dict[str, int]) -> dict[str, int]:
        capped: dict[str, int] = {}

        for category, value in breakdown.items():
            category_cap = MAX_CATEGORY_CONTRIBUTION.get(
                category,
                MAX_CATEGORY_CONTRIBUTION[FindingCategory.GENERAL.value],
            )
            capped[category] = min(value, category_cap)

        return capped

    def _bound_ai_adjustment(self, ai_adjustment: int) -> int:
        return min(max(ai_adjustment, -10), 20)