from pr_sentinel.core.enums import FileChangeStatus
from pr_sentinel.core.models import ChangedFile, PullRequestInfo
from pr_sentinel.diff.changed_file import ChangedFileDiffParser
from pr_sentinel.github.client import GitHubClient
from pr_sentinel.github.models import GitHubChangedFile, GitHubPullRequest


def _normalize_file_status(status: str) -> FileChangeStatus:
    normalized = status.lower().strip()

    if normalized == "added":
        return FileChangeStatus.ADDED

    if normalized == "removed":
        return FileChangeStatus.REMOVED

    if normalized == "renamed":
        return FileChangeStatus.RENAMED

    return FileChangeStatus.MODIFIED


class PullRequestFetcher:
    def __init__(
        self,
        github_client: GitHubClient | None = None,
        diff_parser: ChangedFileDiffParser | None = None,
    ) -> None:
        self.github_client = github_client or GitHubClient()
        self.diff_parser = diff_parser or ChangedFileDiffParser()

    def fetch_pull_request(self, repo_full_name: str, pr_number: int) -> GitHubPullRequest:
        data = self.github_client.get(f"/repos/{repo_full_name}/pulls/{pr_number}")

        return GitHubPullRequest(
            repo_full_name=repo_full_name,
            number=pr_number,
            title=data["title"],
            author=data["user"]["login"],
            base_branch=data["base"]["ref"],
            head_branch=data["head"]["ref"],
            html_url=data.get("html_url"),
        )

    def fetch_changed_files(
        self,
        repo_full_name: str,
        pr_number: int,
    ) -> list[GitHubChangedFile]:
        data = self.github_client.get_paginated(
            f"/repos/{repo_full_name}/pulls/{pr_number}/files"
        )

        changed_files: list[GitHubChangedFile] = []

        for item in data:
            changed_files.append(
                GitHubChangedFile(
                    filename=item["filename"],
                    status=item["status"],
                    additions=item.get("additions", 0),
                    deletions=item.get("deletions", 0),
                    changes=item.get("changes", 0),
                    patch=item.get("patch"),
                    previous_filename=item.get("previous_filename"),
                    raw=item,
                )
            )

        return changed_files

    def fetch(self, repo_full_name: str, pr_number: int) -> PullRequestInfo:
        pr = self.fetch_pull_request(repo_full_name, pr_number)
        files = self.fetch_changed_files(repo_full_name, pr_number)

        changed_files = [
            ChangedFile(
                filename=file.filename,
                status=_normalize_file_status(file.status),
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                patch=file.patch,
                previous_filename=file.previous_filename,
            )
            for file in files
        ]

        parsed_changed_files = self.diff_parser.parse_changed_files(changed_files)

        return PullRequestInfo(
            repo_full_name=pr.repo_full_name,
            pr_number=pr.number,
            title=pr.title,
            author=pr.author,
            base_branch=pr.base_branch,
            head_branch=pr.head_branch,
            html_url=pr.html_url,
            changed_files=parsed_changed_files,
        )