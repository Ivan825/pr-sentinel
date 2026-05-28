from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from pr_sentinel.core.models import AnalysisResult
from pr_sentinel.storage.models import AnalysisRecord, FindingRecord, RepositoryRecord


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def save_analysis(self, result: AnalysisResult) -> AnalysisRecord:
        repository = self._get_or_create_repository(result.pr.repo_full_name)

        risk = result.risk_score

        analysis = AnalysisRecord(
            repository_id=repository.id,
            pr_number=result.pr.pr_number,
            pr_title=result.pr.title,
            pr_author=result.pr.author,
            base_branch=result.pr.base_branch,
            head_branch=result.pr.head_branch,
            html_url=result.pr.html_url,
            findings_count=len(result.findings),
            test_recommendations_count=len(result.test_recommendations),
            risk_score=risk.score if risk else None,
            deterministic_score=risk.deterministic_score if risk else None,
            ai_adjustment=risk.ai_adjustment if risk else 0,
            risk_band=risk.band.value if risk else None,
            summary=result.summary,
            raw_result=result.model_dump(mode="json"),
        )

        self.db.add(analysis)
        self.db.flush()

        for finding in result.findings:
            self.db.add(
                FindingRecord(
                    analysis_id=analysis.id,
                    rule_id=finding.rule_id,
                    title=finding.title,
                    category=finding.category.value,
                    severity=finding.severity.value,
                    source=finding.source,
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                    message=finding.message,
                    evidence=finding.evidence,
                    recommendation=finding.recommendation,
                    confidence=round(finding.confidence * 100),
                )
            )

        self.db.commit()
        self.db.refresh(analysis)

        return analysis

    def list_recent_analyses(self, limit: int = 20) -> list[AnalysisRecord]:
        statement = (
            select(AnalysisRecord)
            .options(joinedload(AnalysisRecord.repository))
            .order_by(desc(AnalysisRecord.created_at))
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def list_repo_analyses(
        self,
        repo_full_name: str,
        limit: int = 20,
    ) -> list[AnalysisRecord]:
        statement = (
            select(AnalysisRecord)
            .options(joinedload(AnalysisRecord.repository))
            .join(RepositoryRecord)
            .where(RepositoryRecord.full_name == repo_full_name)
            .order_by(desc(AnalysisRecord.created_at))
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def _get_or_create_repository(self, repo_full_name: str) -> RepositoryRecord:
        statement = select(RepositoryRecord).where(
            RepositoryRecord.full_name == repo_full_name
        )
        repository = self.db.scalars(statement).first()

        if repository:
            return repository

        repository = RepositoryRecord(full_name=repo_full_name)
        self.db.add(repository)
        self.db.flush()

        return repository