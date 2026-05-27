from typing import Any

from pr_sentinel.github.comment_publisher import (
    PRSENTINEL_COMMENT_MARKER,
    PullRequestCommentPublisher,
)


class FakeGitHubClient:
    def __init__(self, existing_comments: list[dict[str, Any]] | None = None) -> None:
        self.existing_comments = existing_comments or []
        self.post_calls: list[tuple[str, dict[str, Any]]] = []
        self.patch_calls: list[tuple[str, dict[str, Any]]] = []

    def get_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        per_page: int = 100,
        max_pages: int = 10,
    ) -> list[dict[str, Any]]:
        return self.existing_comments

    def post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        self.post_calls.append((path, json_body))
        return {"id": 123, "body": json_body["body"]}

    def patch(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        self.patch_calls.append((path, json_body))
        return {"id": 99, "body": json_body["body"]}


def test_publish_comment_creates_new_comment_when_none_exists() -> None:
    fake_client = FakeGitHubClient()
    publisher = PullRequestCommentPublisher(github_client=fake_client)  # type: ignore[arg-type]

    status = publisher.publish_or_update_comment(
        repo_full_name="example/repo",
        pr_number=7,
        markdown_body="# Report",
    )

    assert status == "created"
    assert len(fake_client.post_calls) == 1
    assert fake_client.patch_calls == []

    path, body = fake_client.post_calls[0]
    assert path == "/repos/example/repo/issues/7/comments"
    assert PRSENTINEL_COMMENT_MARKER in body["body"]
    assert "# Report" in body["body"]


def test_publish_comment_updates_existing_prsentinel_comment() -> None:
    fake_client = FakeGitHubClient(
        existing_comments=[
            {"id": 99, "body": f"{PRSENTINEL_COMMENT_MARKER}\n\nOld report"},
        ]
    )
    publisher = PullRequestCommentPublisher(github_client=fake_client)  # type: ignore[arg-type]

    status = publisher.publish_or_update_comment(
        repo_full_name="example/repo",
        pr_number=7,
        markdown_body="# New Report",
    )

    assert status == "updated"
    assert fake_client.post_calls == []
    assert len(fake_client.patch_calls) == 1

    path, body = fake_client.patch_calls[0]
    assert path == "/repos/example/repo/issues/comments/99"
    assert PRSENTINEL_COMMENT_MARKER in body["body"]
    assert "# New Report" in body["body"]