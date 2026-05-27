from pr_sentinel.core.enums import FileCategory, FileChangeStatus
from pr_sentinel.core.models import (
    AnalysisResult,
    ChangedFile,
    DiffHunk,
    DiffLine,
    PullRequestInfo,
)
from pr_sentinel.llm.context_builder import LlmContextBuilder


def test_llm_context_builder_includes_selected_diff_lines() -> None:
    changed_file = ChangedFile(
        filename="src/AuthFilter.java",
        status=FileChangeStatus.MODIFIED,
        additions=1,
        deletions=1,
        language="Java",
        categories=[FileCategory.AUTH, FileCategory.SECURITY],
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
    context = LlmContextBuilder().build(result)

    assert context.repo_full_name == "example/repo"
    assert len(context.changed_files) == 1
    assert context.changed_files[0].filename == "src/AuthFilter.java"
    assert len(context.changed_files[0].selected_lines) == 2