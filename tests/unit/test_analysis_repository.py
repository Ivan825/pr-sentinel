from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pr_sentinel.core.enums import FindingCategory, RiskBand, Severity
from pr_sentinel.core.models import AnalysisResult, Finding, PullRequestInfo, RiskScore
from pr_sentinel.storage.analysis_repository import AnalysisRepository
from pr_sentinel.storage.database import Base


def test_analysis_repository_saves_analysis_result() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    pr = PullRequestInfo(
        repo_full_name="example/repo",
        pr_number=1,
        title="Test PR",
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
        line_number=1,
        message="Potential secret was added.",
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

    result = AnalysisResult(
        pr=pr,
        findings=[finding],
        test_recommendations=[],
        risk_score=risk_score,
    )

    with TestingSessionLocal() as db:
        repository = AnalysisRepository(db)
        record = repository.save_analysis(result)

        assert record.id is not None
        assert record.pr_number == 1
        assert record.risk_score == 45
        assert record.findings_count == 1

        recent = repository.list_recent_analyses()

        assert len(recent) == 1
        assert recent[0].repository.full_name == "example/repo"