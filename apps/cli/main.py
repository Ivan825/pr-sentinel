import typer
from rich.console import Console
from rich.table import Table

from pr_sentinel.core.config import get_settings
from pr_sentinel.engine.pipeline import AnalysisPipeline
from pr_sentinel.github.client import GitHubClientError
from pr_sentinel.github.pr_fetcher import PullRequestFetcher
from pr_sentinel.reports.analysis_console import print_analysis_result
from pr_sentinel.reports.console import print_pull_request_summary

app = typer.Typer(
    name="pr-sentinel",
    help="PRSentinel — Pull Request Risk Intelligence Platform",
)

console = Console()


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


@app.command("fetch-pr")
def fetch_pr(
    repo: str = typer.Option(
        ...,
        "--repo",
        "-r",
        help="GitHub repository in owner/name format, for example fastapi/fastapi",
    ),
    pr: int = typer.Option(
        ...,
        "--pr",
        "-p",
        help="Pull request number",
    ),
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
    repo: str = typer.Option(
        ...,
        "--repo",
        "-r",
        help="GitHub repository in owner/name format, for example fastapi/fastapi",
    ),
    pr: int = typer.Option(
        ...,
        "--pr",
        "-p",
        help="Pull request number",
    ),
    show_files: bool = typer.Option(
        False,
        "--show-files",
        help="Also print changed-file classification summary before findings.",
    ),
) -> None:
    """Fetch and analyze a GitHub pull request."""
    try:
        fetcher = PullRequestFetcher()
        pull_request = fetcher.fetch(repo_full_name=repo, pr_number=pr)
    except GitHubClientError as exc:
        console.print(f"[bold red]GitHub error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if show_files:
        print_pull_request_summary(pull_request)

    pipeline = AnalysisPipeline()
    result = pipeline.analyze(pull_request)

    print_analysis_result(result)