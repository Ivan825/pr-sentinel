from rich.console import Console
from rich.table import Table

from pr_sentinel.core.models import PullRequestInfo

console = Console()


def print_pull_request_summary(pr: PullRequestInfo) -> None:
    console.print()
    console.print("[bold cyan]PRSentinel Pull Request Fetch Result[/bold cyan]")
    console.print()

    console.print(f"[bold]Repository:[/bold] {pr.repo_full_name}")
    console.print(f"[bold]PR:[/bold] #{pr.pr_number} — {pr.title}")
    console.print(f"[bold]Author:[/bold] {pr.author}")
    console.print(f"[bold]Branches:[/bold] {pr.base_branch} ← {pr.head_branch}")

    if pr.html_url:
        console.print(f"[bold]URL:[/bold] {pr.html_url}")

    console.print()

    table = Table(title="Changed Files")
    table.add_column("File", overflow="fold")
    table.add_column("Status")
    table.add_column("+", justify="right")
    table.add_column("-", justify="right")
    table.add_column("Patch")

    for changed_file in pr.changed_files:
        table.add_row(
            changed_file.filename,
            changed_file.status.value,
            str(changed_file.additions),
            str(changed_file.deletions),
            "yes" if changed_file.patch else "no",
        )

    console.print(table)