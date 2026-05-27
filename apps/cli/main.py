import typer
from rich.console import Console
from rich.table import Table

from pr_sentinel.core.config import get_settings

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