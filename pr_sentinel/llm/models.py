from pydantic import BaseModel, Field

from pr_sentinel.core.enums import FindingCategory, Severity


class LlmDiffLine(BaseModel):
    file_path: str
    old_line_no: int | None = None
    new_line_no: int | None = None
    line_type: str
    content: str


class LlmChangedFileContext(BaseModel):
    filename: str
    language: str | None = None
    categories: list[str] = Field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    selected_lines: list[LlmDiffLine] = Field(default_factory=list)


class LlmFindingContext(BaseModel):
    rule_id: str
    title: str
    category: str
    severity: str
    file_path: str
    line_number: int | None = None
    message: str
    evidence: str | None = None
    recommendation: str | None = None
    confidence: float


class LlmTestRecommendationContext(BaseModel):
    source_file: str
    recommended_tests: list[str] = Field(default_factory=list)
    reason: str


class LlmReviewContext(BaseModel):
    repo_full_name: str
    pr_number: int
    pr_title: str
    author: str
    base_branch: str
    head_branch: str
    deterministic_score: int
    deterministic_findings: list[LlmFindingContext] = Field(default_factory=list)
    test_recommendations: list[LlmTestRecommendationContext] = Field(default_factory=list)
    changed_files: list[LlmChangedFileContext] = Field(default_factory=list)
    instructions: str


class AiSemanticFinding(BaseModel):
    title: str
    category: FindingCategory
    severity: Severity
    file_path: str
    line_number: int | None = None
    message: str
    evidence: str
    recommendation: str
    confidence: float = Field(ge=0.0, le=1.0)


class LlmReviewResult(BaseModel):
    findings: list[AiSemanticFinding] = Field(default_factory=list)
    ai_adjustment: int = Field(default=0, ge=-10, le=20)
    ai_adjustment_reasons: list[str] = Field(default_factory=list)