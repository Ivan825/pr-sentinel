from typing import Any

from pr_sentinel.core.enums import FileCategory, FileChangeStatus
from pr_sentinel.github.pr_fetcher import PullRequestFetcher


class FakeGitHubClient:
    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if path == "/repos/example/repo/pulls/7":
            return {
                "title": "Add auth middleware",
                "user": {"login": "ivan"},
                "base": {"ref": "main"},
                "head": {"ref": "feature/auth"},
                "html_url": "https://github.com/example/repo/pull/7",
            }

        raise AssertionError(f"Unexpected path: {path}")

    def get_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        per_page: int = 100,
        max_pages: int = 10,
    ) -> list[dict[str, Any]]:
        if path == "/repos/example/repo/pulls/7/files":
            return [
                {
                    "filename": "src/main/java/com/app/security/AuthFilter.java",
                    "status": "modified",
                    "additions": 2,
                    "deletions": 1,
                    "changes": 3,
                    "patch": "@@ -1,2 +1,3 @@\n-old\n+new\n+another\n context",
                },
                {
                    "filename": "src/test/java/com/app/security/AuthFilterTest.java",
                    "status": "added",
                    "additions": 2,
                    "deletions": 0,
                    "changes": 2,
                    "patch": "@@ -0,0 +1,2 @@\n+test one\n+test two",
                },
            ]

        raise AssertionError(f"Unexpected path: {path}")


def test_pull_request_fetcher_converts_github_pr_to_internal_model() -> None:
    fetcher = PullRequestFetcher(github_client=FakeGitHubClient())  # type: ignore[arg-type]

    pr = fetcher.fetch("example/repo", 7)

    assert pr.repo_full_name == "example/repo"
    assert pr.pr_number == 7
    assert pr.title == "Add auth middleware"
    assert pr.author == "ivan"
    assert pr.base_branch == "main"
    assert pr.head_branch == "feature/auth"
    assert len(pr.changed_files) == 2

    first_file = pr.changed_files[0]
    assert first_file.filename == "src/main/java/com/app/security/AuthFilter.java"
    assert first_file.status == FileChangeStatus.MODIFIED
    assert first_file.language == "Java"
    assert FileCategory.AUTH in first_file.categories
    assert FileCategory.SECURITY in first_file.categories
    assert FileCategory.BACKEND in first_file.categories
    assert first_file.additions == 2
    assert first_file.deletions == 1
    assert first_file.patch is not None
    assert len(first_file.hunks) == 1
    assert first_file.hunks[0].lines[0].line_type == "deleted"
    assert first_file.hunks[0].lines[1].line_type == "added"

    second_file = pr.changed_files[1]
    assert second_file.status == FileChangeStatus.ADDED
    assert second_file.language == "Java"
    assert FileCategory.TEST in second_file.categories
    assert len(second_file.hunks) == 1
    assert len(second_file.hunks[0].lines) == 2