from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from pr_sentinel.core.config import get_settings
from pr_sentinel.engine.pipeline import AnalysisPipeline
from pr_sentinel.github.client import GitHubClientError
from pr_sentinel.github.comment_publisher import PullRequestCommentPublisher
from pr_sentinel.github.pr_fetcher import PullRequestFetcher
from pr_sentinel.reports.analysis_console import print_analysis_result
from pr_sentinel.reports.console import print_pull_request_summary
from pr_sentinel.reports.json_report import JsonReportGenerator
from pr_sentinel.reports.markdown import MarkdownReportGenerator
from pr_sentinel.reports.sarif import SarifReportGenerator
from pr_sentinel.storage.analysis_repository import AnalysisRepository
from pr_sentinel.storage.database import SessionLocal
from pr_sentinel.storage.persistence import persist_analysis_result

app = typer.Typer(
    name="pr-sentinel",
    help="PRSentinel — Pull Request Risk Intelligence Platform",
)

console = Console()


class OutputFormat(StrEnum):
    CONSOLE = "console"
    MARKDOWN = "markdown"
    JSON = "json"
    SARIF = "sarif"


@app.command()
def version() -> None:
    """Show PRSentinel version and environment."""
    settings = get_settings()

    table = Table(title="PRSentinel")
    table.add_column("Field")
    table.add_column("Value")

    table.add_row("Version", "0.1.0")
    table.add_row("Environment", settings.app_env)
    table.add_row("Debug", str(settings.app_debug))

    console.print(table)


@app.command()
def doctor() -> None:
    """Check local PRSentinel configuration."""
    settings = get_settings()

    console.print("[bold green]PRSentinel Doctor[/bold green]")
    console.print(f"App: {settings.app_name}")
    console.print(f"Environment: {settings.app_env}")
    console.print(f"Database URL configured: {'yes' if settings.database_url else 'no'}")
    console.print(f"GitHub token configured: {'yes' if settings.github_token else 'no'}")
    console.print(f"LLM provider: {settings.llm_provider}")
    console.print(f"LLM model: {settings.llm_model}")


@app.command("fetch-pr")
def fetch_pr(
    repo: Annotated[
        str,
        typer.Option(
            "--repo",
            "-r",
            help="GitHub repository in owner/name format, for example fastapi/fastapi",
        ),
    ],
    pr: Annotated[
        int,
        typer.Option(
            "--pr",
            "-p",
            help="Pull request number",
        ),
    ],
) -> None:
    """Fetch GitHub pull request metadata and changed files."""
    try:
        fetcher = PullRequestFetcher()
        pull_request = fetcher.fetch(repo_full_name=repo, pr_number=pr)
    except GitHubClientError as exc:
        console.print(f"[bold red]GitHub error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    print_pull_request_summary(pull_request)


@app.command("analyze-pr")
def analyze_pr(
    repo: Annotated[
        str,
        typer.Option(
            "--repo",
            "-r",
            help="GitHub repository in owner/name format, for example fastapi/fastapi",
        ),
    ],
    pr: Annotated[
        int,
        typer.Option(
            "--pr",
            "-p",
            help="Pull request number",
        ),
    ],
    show_files: Annotated[
        bool,
        typer.Option(
            "--show-files",
            help="Also print changed-file classification summary before findings.",
        ),
    ] = False,
    output_format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Output format: console, markdown, json, or sarif.",
        ),
    ] = OutputFormat.CONSOLE,
    output_path: Annotated[
        Path | None,
        typer.Option(
            "--out",
            "-o",
            help="Optional output file path for markdown/json/sarif reports.",
        ),
    ] = None,
    post_comment: Annotated[
        bool,
        typer.Option(
            "--post-comment",
            help="Post or update the PRSentinel Markdown report as a GitHub PR comment.",
        ),
    ] = False,
    use_llm: Annotated[
        bool,
        typer.Option(
            "--use-llm",
            help="Enable AI-assisted semantic review using the configured LLM provider.",
        ),
    ] = False,
    save: Annotated[
        bool,
        typer.Option(
            "--save",
            help="Persist the analysis result to PostgreSQL.",
        ),
    ] = False,
) -> None:
    """Fetch and analyze a GitHub pull request."""
    try:
        fetcher = PullRequestFetcher()
        pull_request = fetcher.fetch(repo_full_name=repo, pr_number=pr)
    except GitHubClientError as exc:
        console.print(f"[bold red]GitHub error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if show_files and output_format == OutputFormat.CONSOLE:
        print_pull_request_summary(pull_request)

    pipeline = AnalysisPipeline(use_llm=use_llm)
    result = pipeline.analyze(pull_request)

    if save:
        analysis_id = persist_analysis_result(result)
        console.print(f"[bold green]Analysis saved with ID:[/bold green] {analysis_id}")

    markdown_report = MarkdownReportGenerator().generate(result)

    if post_comment:
        try:
            status = PullRequestCommentPublisher().publish_or_update_comment(
                repo_full_name=repo,
                pr_number=pr,
                markdown_body=markdown_report,
            )
        except GitHubClientError as exc:
            console.print(f"[bold red]GitHub comment error:[/bold red] {exc}")
            raise typer.Exit(code=1) from exc

        console.print(f"[bold green]GitHub PR comment {status}.[/bold green]")

    if output_format == OutputFormat.CONSOLE:
        print_analysis_result(result)
        return

    if output_format == OutputFormat.MARKDOWN:
        content = markdown_report
    elif output_format == OutputFormat.JSON:
        content = JsonReportGenerator().generate_json(result)
    else:
        content = SarifReportGenerator().generate_json(result)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        console.print(f"[bold green]Report written to:[/bold green] {output_path}")
        return

    console.print(content)


@app.command("list-analyses")
def list_analyses(
    repo: Annotated[
        str | None,
        typer.Option(
            "--repo",
            "-r",
            help="Optional repository filter in owner/name format.",
        ),
    ] = None,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-n",
            help="Maximum number of analyses to show.",
        ),
    ] = 20,
) -> None:
    """List recently saved PRSentinel analyses."""
    with SessionLocal() as db:
        repository = AnalysisRepository(db)

        if repo:
            analyses = repository.list_repo_analyses(repo_full_name=repo, limit=limit)
        else:
            analyses = repository.list_recent_analyses(limit=limit)

    table = Table(title="Saved Analyses")
    table.add_column("ID", justify="right")
    table.add_column("Repository")
    table.add_column("PR", justify="right")
    table.add_column("Risk")
    table.add_column("Score", justify="right")
    table.add_column("Findings", justify="right")
    table.add_column("Created At")

    for analysis in analyses:
        table.add_row(
            str(analysis.id),
            analysis.repository.full_name,
            str(analysis.pr_number),
            analysis.risk_band or "-",
            str(analysis.risk_score if analysis.risk_score is not None else "-"),
            str(analysis.findings_count),
            analysis.created_at.isoformat(),
        )

    console.print(table)