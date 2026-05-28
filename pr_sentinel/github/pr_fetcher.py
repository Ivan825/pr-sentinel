from typing import Any

from pr_sentinel.classifier.file_classifier import FileClassifier
from pr_sentinel.classifier.language_detector import detect_language
from pr_sentinel.core.enums import FileChangeStatus
from pr_sentinel.core.models import ChangedFile, DiffHunk, DiffLine, PullRequestInfo
from pr_sentinel.github.client import GitHubClient


class PullRequestFetcher:
    def __init__(self, github_client: GitHubClient | None = None) -> None:
        self.github_client = github_client or GitHubClient()
        self.file_classifier = FileClassifier()

    def fetch(self, repo_full_name: str, pr_number: int) -> PullRequestInfo:
        pr_payload = self.github_client.get(f"/repos/{repo_full_name}/pulls/{pr_number}")
        files_payload = self.github_client.get_paginated(
            f"/repos/{repo_full_name}/pulls/{pr_number}/files"
        )

        return PullRequestInfo(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            title=str(pr_payload.get("title", "")),
            author=str(pr_payload.get("user", {}).get("login", "")),
            base_branch=str(pr_payload.get("base", {}).get("ref", "")),
            head_branch=str(pr_payload.get("head", {}).get("ref", "")),
            html_url=pr_payload.get("html_url"),
            changed_files=[
                self._to_changed_file(file_payload) for file_payload in files_payload
            ],
        )

    def _to_changed_file(self, file_payload: dict[str, Any]) -> ChangedFile:
        filename = str(file_payload.get("filename", ""))
        patch = file_payload.get("patch")

        changed_file = ChangedFile(
            filename=filename,
            status=self._map_status(str(file_payload.get("status", "modified"))),
            additions=int(file_payload.get("additions", 0)),
            deletions=int(file_payload.get("deletions", 0)),
            changes=int(file_payload.get("changes", 0)),
            patch=patch if isinstance(patch, str) else None,
            previous_filename=file_payload.get("previous_filename"),
            language=detect_language(filename),
            categories=[],
            hunks=self._parse_patch(patch) if isinstance(patch, str) else [],
        )

        return self.file_classifier.classify(changed_file)

    def _map_status(self, status: str) -> FileChangeStatus:
        normalized = status.lower()

        if normalized == "added":
            return FileChangeStatus.ADDED

        if normalized == "removed":
            return FileChangeStatus.REMOVED

        if normalized == "renamed":
            return FileChangeStatus.RENAMED

        return FileChangeStatus.MODIFIED

    def _parse_patch(self, patch: str) -> list[DiffHunk]:
        hunks: list[DiffHunk] = []
        current_hunk: DiffHunk | None = None
        old_line_no = 0
        new_line_no = 0

        for raw_line in patch.splitlines():
            if raw_line.startswith("@@"):
                current_hunk = self._parse_hunk_header(raw_line)
                hunks.append(current_hunk)
                old_line_no = current_hunk.old_start
                new_line_no = current_hunk.new_start
                continue

            if current_hunk is None:
                continue

            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                current_hunk.lines.append(
                    DiffLine(
                        old_line_no=None,
                        new_line_no=new_line_no,
                        content=raw_line[1:],
                        line_type="added",
                    )
                )
                new_line_no += 1
                continue

            if raw_line.startswith("-") and not raw_line.startswith("---"):
                current_hunk.lines.append(
                    DiffLine(
                        old_line_no=old_line_no,
                        new_line_no=None,
                        content=raw_line[1:],
                        line_type="deleted",
                    )
                )
                old_line_no += 1
                continue

            if raw_line.startswith("\\"):
                continue

            content = raw_line[1:] if raw_line.startswith(" ") else raw_line
            current_hunk.lines.append(
                DiffLine(
                    old_line_no=old_line_no,
                    new_line_no=new_line_no,
                    content=content,
                    line_type="context",
                )
            )
            old_line_no += 1
            new_line_no += 1

        return hunks

    def _parse_hunk_header(self, header: str) -> DiffHunk:
        parts = header.split("@@")
        range_part = parts[1].strip() if len(parts) > 1 else ""
        section_header = parts[2].strip() if len(parts) > 2 else None

        old_range = "0,0"
        new_range = "0,0"

        tokens = range_part.split()

        if len(tokens) >= 2:
            old_range = tokens[0].removeprefix("-")
            new_range = tokens[1].removeprefix("+")

        old_start, old_count = self._parse_range(old_range)
        new_start, new_count = self._parse_range(new_range)

        return DiffHunk(
            old_start=old_start,
            old_count=old_count,
            new_start=new_start,
            new_count=new_count,
            section_header=section_header,
            lines=[],
        )

    def _parse_range(self, range_text: str) -> tuple[int, int]:
        if "," not in range_text:
            return int(range_text), 1

        start, count = range_text.split(",", maxsplit=1)

        return int(start), int(count)