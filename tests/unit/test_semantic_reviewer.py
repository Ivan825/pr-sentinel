from typing import Any

from pr_sentinel.core.enums import FileCategory, FileChangeStatus, FindingCategory, Severity
from pr_sentinel.core.models import (
    AnalysisResult,
    ChangedFile,
    DiffHunk,
    DiffLine,
    PullRequestInfo,
)
from pr_sentinel.llm.semantic_reviewer import SemanticReviewer


class FakeLlmClient:
    def review(self, context: dict[str, Any]) -> dict[str, Any]:
        return {
            "findings": [
                {
                    "title": "Authorization appears weakened",
                    "category": "AUTH",
                    "severity": "HIGH",
                    "file_path": "src/AuthFilter.java",
                    "line_number": 10,
                    "message": (
                        "Admin-only authorization appears to be replaced by "
                        "unconditional allow."
                    ),
                    "evidence": "Deleted hasRole('ADMIN'), added return true.",
                    "recommendation": "Restore role check or add explicit authorization tests.",
                    "confidence": 0.86,
                }
            ],
            "ai_adjustment": 10,
            "ai_adjustment_reasons": ["Authorization semantics appear weaker."],
        }


def test_semantic_reviewer_accepts_evidence_backed_finding() -> None:
    changed_file = ChangedFile(
        filename="src/AuthFilter.java",
        status=FileChangeStatus.MODIFIED,
        additions=1,
        deletions=1,
        language="Java",
        categories=[FileCategory.AUTH],
        hunks=[
            DiffHunk(
                old_start=10,
                old_count=1,
                new_start=10,
                new_count=1,
                lines=[
                    DiffLine(
                        old_line_no=10,
                        new_line_no=None,
                        content="if (!hasRole('ADMIN')) throw new ForbiddenException();",
                        line_type="deleted",
                    ),
                    DiffLine(
                        old_line_no=None,
                        new_line_no=10,
                        content="return true;",
                        line_type="added",
                    ),
                ],
            )
        ],
    )

    pr = PullRequestInfo(
        repo_full_name="example/repo",
        pr_number=1,
        title="Change auth",
        author="ivan",
        base_branch="main",
        head_branch="feature",
        changed_files=[changed_file],
    )

    result = AnalysisResult(pr=pr)

    reviewer = SemanticReviewer(llm_client=FakeLlmClient())  # type: ignore[arg-type]
    review_result = reviewer.review(result)
    core_findings = reviewer.to_core_findings(review_result)

    assert len(core_findings) == 1
    assert core_findings[0].source == "AI_ASSISTED"
    assert core_findings[0].category == FindingCategory.AUTH
    assert core_findings[0].severity == Severity.HIGH
    assert review_result.ai_adjustment == 10