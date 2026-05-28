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