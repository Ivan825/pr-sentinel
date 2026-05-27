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

    if result.risk_score:
        console.print(
            f"[bold]Risk:[/bold] {result.risk_score.band.value} — "
            f"{result.risk_score.score}/100"
        )
        console.print(
            f"[bold]Deterministic Score:[/bold] "
            f"{result.risk_score.deterministic_score}/100"
        )

        if result.risk_score.ai_adjustment:
            console.print(f"[bold]AI Adjustment:[/bold] {result.risk_score.ai_adjustment}")

        if result.risk_score.breakdown:
            console.print()
            _print_risk_breakdown(result)

    console.print()

    if not result.findings:
        console.print(
            "[bold green]No findings detected by current deterministic rules.[/bold green]"
        )
        return

    _print_findings(result)


def _print_risk_breakdown(result: AnalysisResult) -> None:
    if not result.risk_score:
        return

    table = Table(title="Risk Breakdown")
    table.add_column("Category")
    table.add_column("Contribution", justify="right")

    for category, contribution in sorted(
        result.risk_score.breakdown.items(),
        key=lambda item: item[1],
        reverse=True,
    ):
        table.add_row(category, f"+{contribution}")

    console.print(table)


def _print_findings(result: AnalysisResult) -> None:
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