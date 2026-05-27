from pydantic import BaseModel, Field

from pr_sentinel.core.enums import (
    FileCategory,
    FileChangeStatus,
    FindingCategory,
    RiskBand,
    Severity,
)


class DiffLine(BaseModel):
    old_line_no: int | None = None
    new_line_no: int | None = None
    content: str
    line_type: str


class DiffHunk(BaseModel):
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    section_header: str | None = None
    lines: list[DiffLine] = Field(default_factory=list)


class ChangedFile(BaseModel):
    filename: str
    status: FileChangeStatus
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: str | None = None
    previous_filename: str | None = None

    language: str | None = None
    categories: list[FileCategory] = Field(default_factory=list)
    hunks: list[DiffHunk] = Field(default_factory=list)


class PullRequestInfo(BaseModel):
    repo_full_name: str
    pr_number: int
    title: str
    author: str
    base_branch: str
    head_branch: str
    html_url: str | None = None
    changed_files: list[ChangedFile] = Field(default_factory=list)


class Finding(BaseModel):
    rule_id: str
    title: str
    category: FindingCategory
    severity: Severity
    file_path: str
    line_number: int | None = None
    message: str
    evidence: str | None = None
    recommendation: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = "DETERMINISTIC"


class TestRecommendation(BaseModel):
    source_file: str
    recommended_tests: list[str] = Field(default_factory=list)
    reason: str


class RiskScore(BaseModel):
    score: int = Field(ge=0, le=100)
    band: RiskBand
    breakdown: dict[str, int] = Field(default_factory=dict)

    deterministic_score: int = Field(ge=0, le=100)
    ai_adjustment: int = 0
    ai_adjustment_reasons: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    pr: PullRequestInfo
    findings: list[Finding] = Field(default_factory=list)
    test_recommendations: list[TestRecommendation] = Field(default_factory=list)
    risk_score: RiskScore | None = None
    summary: str | None = None