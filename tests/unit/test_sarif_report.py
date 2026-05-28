import json

from pr_sentinel.core.enums import FindingCategory, RiskBand, Severity
from pr_sentinel.core.models import AnalysisResult, Finding, PullRequestInfo, RiskScore
from pr_sentinel.reports.sarif import SarifReportGenerator


def test_sarif_report_generator_outputs_valid_sarif_shape() -> None:
    result = _sample_result()

    report = SarifReportGenerator().generate_json(result)
    parsed = json.loads(report)

    assert parsed["version"] == "2.1.0"
    assert len(parsed["runs"]) == 1

    run = parsed["runs"][0]

    assert run["tool"]["driver"]["name"] == "PRSentinel"
    assert run["properties"]["repository"] == "example/repo"
    assert run["properties"]["riskScore"] == 45

    assert len(run["tool"]["driver"]["rules"]) == 1
    assert run["tool"]["driver"]["rules"][0]["id"] == "SEC_001_HARDCODED_SECRET"

    assert len(run["results"]) == 1
    assert run["results"][0]["ruleId"] == "SEC_001_HARDCODED_SECRET"
    assert run["results"][0]["level"] == "error"

    artifact_uri = run["results"][0]["locations"][0]["physicalLocation"][
        "artifactLocation"
    ]["uri"]

    assert artifact_uri == "src/config.py"


def _sample_result() -> AnalysisResult:
    pr = PullRequestInfo(
        repo_full_name="example/repo",
        pr_number=1,
        title="Risky config",
        author="contributor",
        base_branch="main",
        head_branch="feature",
        changed_files=[],
    )

    finding = Finding(
        rule_id="SEC_001_HARDCODED_SECRET",
        title="Hardcoded secret detected",
        category=FindingCategory.SECURITY,
        severity=Severity.CRITICAL,
        file_path="src/config.py",
        line_number=4,
        message="Potential secret was added.",
        evidence='token = "ghp_example"',
        recommendation="Remove the secret and rotate it.",
        confidence=0.9,
    )

    risk_score = RiskScore(
        score=45,
        band=RiskBand.MEDIUM,
        breakdown={"SECURITY": 45},
        deterministic_score=45,
        ai_adjustment=0,
        ai_adjustment_reasons=[],
    )

    return AnalysisResult(
        pr=pr,
        findings=[finding],
        test_recommendations=[],
        risk_score=risk_score,
    )