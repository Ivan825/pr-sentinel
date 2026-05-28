from typing import Any

from fastapi import APIRouter, HTTPException, Query

from apps.api.schemas import SavedAnalysisDetail, SavedAnalysisSummary
from pr_sentinel.storage.analysis_repository import AnalysisRepository
from pr_sentinel.storage.database import SessionLocal
from pr_sentinel.storage.models import AnalysisRecord, FindingRecord

router = APIRouter(prefix="/api", tags=["saved-analyses"])


@router.get("/analyses", response_model=list[SavedAnalysisSummary])
def list_recent_analyses(
    limit: int = Query(default=20, ge=1, le=100),
) -> list[SavedAnalysisSummary]:
    with SessionLocal() as db:
        repository = AnalysisRepository(db)
        analyses = repository.list_recent_analyses(limit=limit)

        return [_to_summary(analysis) for analysis in analyses]


@router.get(
    "/repositories/{owner}/{repo}/analyses",
    response_model=list[SavedAnalysisSummary],
)
def list_repository_analyses(
    owner: str,
    repo: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[SavedAnalysisSummary]:
    repo_full_name = f"{owner}/{repo}"

    with SessionLocal() as db:
        repository = AnalysisRepository(db)
        analyses = repository.list_repo_analyses(
            repo_full_name=repo_full_name,
            limit=limit,
        )

        return [_to_summary(analysis) for analysis in analyses]


@router.get("/analyses/{analysis_id}", response_model=SavedAnalysisDetail)
def get_analysis_detail(analysis_id: int) -> SavedAnalysisDetail:
    with SessionLocal() as db:
        repository = AnalysisRepository(db)
        analysis = repository.get_analysis_by_id(analysis_id)

        if analysis is None:
            raise HTTPException(status_code=404, detail="Analysis not found")

        return SavedAnalysisDetail(
            summary=_to_summary(analysis),
            raw_result=analysis.raw_result,
            findings=[_finding_to_dict(finding) for finding in analysis.findings],
        )


def _to_summary(analysis: AnalysisRecord) -> SavedAnalysisSummary:
    return SavedAnalysisSummary(
        id=analysis.id,
        repository=analysis.repository.full_name,
        pr_number=analysis.pr_number,
        pr_title=analysis.pr_title,
        pr_author=analysis.pr_author,
        base_branch=analysis.base_branch,
        head_branch=analysis.head_branch,
        risk_score=analysis.risk_score,
        risk_band=analysis.risk_band,
        deterministic_score=analysis.deterministic_score,
        ai_adjustment=analysis.ai_adjustment,
        findings_count=analysis.findings_count,
        test_recommendations_count=analysis.test_recommendations_count,
        created_at=analysis.created_at.isoformat(),
    )


def _finding_to_dict(finding: FindingRecord) -> dict[str, Any]:
    return {
        "id": finding.id,
        "rule_id": finding.rule_id,
        "title": finding.title,
        "category": finding.category,
        "severity": finding.severity,
        "source": finding.source,
        "file_path": finding.file_path,
        "line_number": finding.line_number,
        "message": finding.message,
        "evidence": finding.evidence,
        "recommendation": finding.recommendation,
        "confidence": finding.confidence,
        "created_at": finding.created_at.isoformat(),
    }