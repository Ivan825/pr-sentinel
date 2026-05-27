from pr_sentinel.core.enums import FindingCategory, RiskBand, Severity
from pr_sentinel.core.models import Finding
from pr_sentinel.risk.scorer import RiskScorer, determine_risk_band


def test_determine_risk_band() -> None:
    assert determine_risk_band(0) == RiskBand.LOW
    assert determine_risk_band(29) == RiskBand.LOW
    assert determine_risk_band(30) == RiskBand.MEDIUM
    assert determine_risk_band(59) == RiskBand.MEDIUM
    assert determine_risk_band(60) == RiskBand.HIGH
    assert determine_risk_band(79) == RiskBand.HIGH
    assert determine_risk_band(80) == RiskBand.CRITICAL
    assert determine_risk_band(100) == RiskBand.CRITICAL


def test_risk_scorer_scores_security_secret_as_high_risk() -> None:
    finding = Finding(
        rule_id="SEC_001_HARDCODED_SECRET",
        title="Hardcoded secret detected",
        category=FindingCategory.SECURITY,
        severity=Severity.CRITICAL,
        file_path="src/config.ts",
        line_number=1,
        message="Potential GitHub token was added.",
        evidence='const token = "ghp_xxx"',
        recommendation="Remove the secret.",
        confidence=0.9,
    )

    score = RiskScorer().score_findings([finding])

    assert score.score >= 40
    assert score.deterministic_score == score.score
    assert score.ai_adjustment == 0
    assert score.band in {RiskBand.MEDIUM, RiskBand.HIGH, RiskBand.CRITICAL}
    assert "SECURITY" in score.breakdown


def test_risk_scorer_bounds_ai_adjustment() -> None:
    finding = Finding(
        rule_id="DEP_001_DEPENDENCY_FILE_CHANGED",
        title="Dependency file changed",
        category=FindingCategory.DEPENDENCY,
        severity=Severity.MEDIUM,
        file_path="package.json",
        message="Dependency file changed.",
        confidence=1.0,
    )

    positive = RiskScorer().score_findings([finding], ai_adjustment=100)
    negative = RiskScorer().score_findings([finding], ai_adjustment=-100)

    assert positive.ai_adjustment == 20
    assert negative.ai_adjustment == -10


def test_empty_findings_scores_low_zero() -> None:
    score = RiskScorer().score_findings([])

    assert score.score == 0
    assert score.deterministic_score == 0
    assert score.band == RiskBand.LOW
    assert score.breakdown == {}