from rich.console import Console
from rich.table import Table

from pr_sentinel.core.models import AnalysisResult

console = Console()


def print_analysis_result(result: AnalysisResult) -> None:
    console.print()
    console.print("[bold cyan]PRSentinel Analysis Result[/bold cyan]")
    console.print()

    console.print(f"[bold]Repository:[/bold] {result.pr.repo_full_name}")
    console.print(f"[bold]PR:[/bold] #{result.pr.pr_number} — {result.pr.title}")
    console.print(f"[bold]Author:[/bold] {result.pr.author}")
    console.print(f"[bold]Findings:[/bold] {len(result.findings)}")
    console.print()

    if not result.findings:
        console.print(
            "[bold green]No findings detected by current deterministic rules.[/bold green]"
        )
        return

    table = Table(title="Findings")
    table.add_column("Severity")
    table.add_column("Source")
    table.add_column("Rule")
    table.add_column("File", overflow="fold")
    table.add_column("Line", justify="right")
    table.add_column("Message", overflow="fold")

    for finding in result.findings:
        table.add_row(
            finding.severity.value,
            finding.source,
            finding.rule_id,
            finding.file_path,
            str(finding.line_number) if finding.line_number is not None else "-",
            finding.message,
        )

    console.print(table)