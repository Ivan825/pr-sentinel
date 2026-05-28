from typing import Any

from pydantic import BaseModel, Field


class AnalyzePullRequestRequest(BaseModel):
    repo: str = Field(..., description="GitHub repository in owner/name format")
    pr: int = Field(..., description="Pull request number")
    use_llm: bool = False
    post_comment: bool = False
    save: bool = False


class AnalyzePullRequestResponse(BaseModel):
    repo: str
    pr: int
    findings_count: int
    test_recommendations_count: int
    risk_score: int
    risk_band: str
    deterministic_score: int
    ai_adjustment: int
    comment_status: str | None = None
    analysis_id: int | None = None
    analysis: dict[str, Any]


class SavedAnalysisSummary(BaseModel):
    id: int
    repository: str
    pr_number: int
    pr_title: str
    pr_author: str
    base_branch: str
    head_branch: str
    risk_score: int | None = None
    risk_band: str | None = None
    deterministic_score: int | None = None
    ai_adjustment: int
    findings_count: int
    test_recommendations_count: int
    created_at: str


class SavedAnalysisDetail(BaseModel):
    summary: SavedAnalysisSummary
    raw_result: dict[str, Any]
    findings: list[dict[str, Any]]