from pr_sentinel.core.models import DiffHunk
from pr_sentinel.diff.hunk import DiffParseError, parse_hunk_header, parse_hunk_lines


class PatchParser:
    def parse_patch(self, patch: str | None) -> list[DiffHunk]:
        if not patch:
            return []

        lines = patch.splitlines()
        hunks: list[DiffHunk] = []

        current_header: str | None = None
        current_lines: list[str] = []

        for line in lines:
            if line.startswith("@@"):
                if current_header is not None:
                    hunks.append(self._build_hunk(current_header, current_lines))

                current_header = line
                current_lines = []
            else:
                if current_header is not None:
                    current_lines.append(line)

        if current_header is not None:
            hunks.append(self._build_hunk(current_header, current_lines))

        return hunks

    def _build_hunk(self, header: str, lines: list[str]) -> DiffHunk:
        try:
            hunk = parse_hunk_header(header)
            return parse_hunk_lines(hunk, lines)
        except DiffParseError:
            raise