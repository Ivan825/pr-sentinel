from typing import Any

from pr_sentinel.core.enums import FileChangeStatus
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
                    "filename": "src/security/AuthFilter.java",
                    "status": "modified",
                    "additions": 12,
                    "deletions": 4,
                    "changes": 16,
                    "patch": "@@ -1,2 +1,2 @@\n-old\n+new",
                },
                {
                    "filename": "src/test/AuthFilterTest.java",
                    "status": "added",
                    "additions": 40,
                    "deletions": 0,
                    "changes": 40,
                    "patch": "@@ -0,0 +1,2 @@\n+test",
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
    assert first_file.filename == "src/security/AuthFilter.java"
    assert first_file.status == FileChangeStatus.MODIFIED
    assert first_file.additions == 12
    assert first_file.deletions == 4
    assert first_file.patch is not None

    second_file = pr.changed_files[1]
    assert second_file.status == FileChangeStatus.ADDED