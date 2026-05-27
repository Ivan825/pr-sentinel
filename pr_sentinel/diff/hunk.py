import re

from pr_sentinel.core.models import DiffHunk, DiffLine

HUNK_HEADER_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? "
    r"\+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
    r"(?: (?P<section>.*))?$"
)


class DiffParseError(ValueError):
    pass


def parse_hunk_header(header: str) -> DiffHunk:
    match = HUNK_HEADER_RE.match(header)

    if not match:
        raise DiffParseError(f"Invalid hunk header: {header}")

    old_start = int(match.group("old_start"))
    old_count = int(match.group("old_count") or "1")
    new_start = int(match.group("new_start"))
    new_count = int(match.group("new_count") or "1")
    section_header = match.group("section")

    return DiffHunk(
        old_start=old_start,
        old_count=old_count,
        new_start=new_start,
        new_count=new_count,
        section_header=section_header,
        lines=[],
    )


def parse_hunk_lines(hunk: DiffHunk, raw_lines: list[str]) -> DiffHunk:
    old_line_no = hunk.old_start
    new_line_no = hunk.new_start

    parsed_lines: list[DiffLine] = []

    for raw_line in raw_lines:
        if raw_line.startswith("\\ No newline at end of file"):
            continue

        if raw_line.startswith("+"):
            parsed_lines.append(
                DiffLine(
                    old_line_no=None,
                    new_line_no=new_line_no,
                    content=raw_line[1:],
                    line_type="added",
                )
            )
            new_line_no += 1
            continue

        if raw_line.startswith("-"):
            parsed_lines.append(
                DiffLine(
                    old_line_no=old_line_no,
                    new_line_no=None,
                    content=raw_line[1:],
                    line_type="deleted",
                )
            )
            old_line_no += 1
            continue

        if raw_line.startswith(" "):
            parsed_lines.append(
                DiffLine(
                    old_line_no=old_line_no,
                    new_line_no=new_line_no,
                    content=raw_line[1:],
                    line_type="context",
                )
            )
            old_line_no += 1
            new_line_no += 1
            continue

        parsed_lines.append(
            DiffLine(
                old_line_no=old_line_no,
                new_line_no=new_line_no,
                content=raw_line,
                line_type="context",
            )
        )
        old_line_no += 1
        new_line_no += 1

    hunk.lines = parsed_lines
    return hunk