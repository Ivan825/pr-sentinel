from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.main import app
from pr_sentinel.core.enums import FindingCategory, RiskBand, Severity
from pr_sentinel.core.models import AnalysisResult, Finding, PullRequestInfo, RiskScore
from pr_sentinel.storage.analysis_repository import AnalysisRepository
from pr_sentinel.storage.database import Base


def test_saved_analyses_api_lists_and_reads_saved_analysis(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    with testing_session_local() as db:
        repository = AnalysisRepository(db)
        repository.save_analysis(_sample_result())

    class FakeSessionLocal:
        db: Session

        def __enter__(self) -> Session:
            self.db = testing_session_local()
            return self.db

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
            self.db.close()

    import apps.api.routes.analyses as analyses_route

    monkeypatch.setattr(
        analyses_route,
        "SessionLocal",
        FakeSessionLocal,
    )

    client = TestClient(app)

    list_response = client.get("/api/analyses")
    assert list_response.status_code == 200

    analyses = list_response.json()
    assert len(analyses) == 1
    assert analyses[0]["repository"] == "example/repo"

    analysis_id = analyses[0]["id"]

    detail_response = client.get(f"/api/analyses/{analysis_id}")
    assert detail_response.status_code == 200

    detail = detail_response.json()
    assert detail["summary"]["id"] == analysis_id
    assert detail["raw_result"]["pr"]["repo_full_name"] == "example/repo"
    assert len(detail["findings"]) == 1


def _sample_result() -> AnalysisResult:
    pr = PullRequestInfo(
        repo_full_name="example/repo",
        pr_number=1,
        title="Saved PR",
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

    return AnalysisResult(
        pr=pr,
        findings=[finding],
        test_recommendations=[],
        risk_score=risk_score,
    )