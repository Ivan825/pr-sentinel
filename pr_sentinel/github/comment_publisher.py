from typing import Any

from pr_sentinel.github.client import GitHubClient, GitHubClientError

PRSENTINEL_COMMENT_MARKER = "<!-- pr-sentinel-report -->"


class PullRequestCommentPublisher:
    def __init__(self, github_client: GitHubClient | None = None) -> None:
        self.github_client = github_client or GitHubClient()

    def publish_or_update_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        markdown_body: str,
    ) -> str:
        body = self._with_marker(markdown_body)
        existing_comment = self._find_existing_prsentinel_comment(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
        )

        if existing_comment:
            comment_id = existing_comment["id"]

            try:
                self.github_client.patch(
                    f"/repos/{repo_full_name}/issues/comments/{comment_id}",
                    json_body={"body": body},
                )
                return "updated"
            except GitHubClientError as exc:
                if not self._is_cross_actor_comment_update_error(exc):
                    raise

        self.github_client.post(
            f"/repos/{repo_full_name}/issues/{pr_number}/comments",
            json_body={"body": body},
        )
        return "created"

    def _find_existing_prsentinel_comment(
        self,
        repo_full_name: str,
        pr_number: int,
    ) -> dict[str, Any] | None:
        comments = self.github_client.get_paginated(
            f"/repos/{repo_full_name}/issues/{pr_number}/comments"
        )

        for comment in reversed(comments):
            body = str(comment.get("body", ""))

            if PRSENTINEL_COMMENT_MARKER in body:
                return comment

        return None

    def _with_marker(self, markdown_body: str) -> str:
        if PRSENTINEL_COMMENT_MARKER in markdown_body:
            return markdown_body

        return f"{PRSENTINEL_COMMENT_MARKER}\n\n{markdown_body}"

    def _is_cross_actor_comment_update_error(self, exc: GitHubClientError) -> bool:
        error_text = str(exc).lower()

        return (
            "403" in error_text
            and "resource not accessible by integration" in error_text
            and "issues/comments" in error_text
        )