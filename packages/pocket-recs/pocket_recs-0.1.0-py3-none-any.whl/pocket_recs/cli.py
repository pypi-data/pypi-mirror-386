"""Command-line interface for pocket-recs."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from pocket_recs.offline.fit import fit
from pocket_recs.online.recommender import Recommender
from pocket_recs.types import RecommendRequest

app = typer.Typer(
    name="pocket-recs",
    help="CPU-only hybrid recommender system",
    no_args_is_help=True,
)
console = Console()


@app.command("fit")
def run_fit(
    interactions: str = typer.Argument(..., help="Path to interactions Parquet file"),
    catalog: str = typer.Argument(..., help="Path to catalog CSV file"),
    out_dir: str = typer.Argument(..., help="Output directory for artifacts"),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Embedding model name (default: all-MiniLM-L6-v2)",
    ),
) -> None:
    """
    Run offline training pipeline to generate artifacts.

    Example:
        pocket-recs fit interactions.parquet catalog.csv artifacts/
    """
    try:
        artifact_dir = fit(
            interactions_path=interactions,
            catalog_path=catalog,
            out_dir=out_dir,
            model_name=model,
        )
        console.print(f"[bold green]Success![/bold green] Artifacts written to: {artifact_dir}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("recommend")
def run_recommend(
    artifacts: str = typer.Argument(..., help="Path to artifacts directory"),
    catalog: str = typer.Argument(..., help="Path to catalog CSV file"),
    user_id: str = typer.Option("user_001", "--user", "-u", help="User ID"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Filter by brand"),
    k: int = typer.Option(10, "--top-k", "-k", help="Number of recommendations"),
) -> None:
    """
    Generate recommendations for a user (demo).

    Example:
        pocket-recs recommend artifacts/ catalog.csv --user u123 --top-k 10
    """
    try:
        recommender = Recommender(artifacts, catalog)

        request = RecommendRequest(user_id=user_id, brand=brand, k=k, recent=[])
        response = recommender.recommend(request)

        table = Table(title=f"Recommendations for {user_id}")
        table.add_column("Rank", style="cyan", justify="right")
        table.add_column("Item ID", style="magenta")
        table.add_column("Score", style="green", justify="right")
        table.add_column("Reasons", style="yellow")

        for item in response.items:
            table.add_row(
                str(item.rank),
                item.item_id,
                f"{item.score:.4f}",
                ", ".join(item.reasons),
            )

        console.print(table)
        console.print(f"\nArtifact version: {response.artifact_version}")
        console.print(f"Request ID: {response.request_id}")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("serve")
def run_serve(
    artifacts: str = typer.Argument(..., help="Path to artifacts directory"),
    catalog: str = typer.Argument(..., help="Path to catalog CSV file"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host address"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
) -> None:
    """
    Start FastAPI server for recommendation API.

    Example:
        pocket-recs serve artifacts/ catalog.csv --port 8000
    """
    try:
        import uvicorn

        from pocket_recs.api.app import create_app

        app_instance = create_app(artifacts, catalog)

        console.print(f"[bold blue]Starting server on {host}:{port}[/bold blue]")
        console.print(f"Docs available at: http://{host}:{port}/docs")

        uvicorn.run(
            app_instance,
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )
    except ImportError:
        console.print(
            "[bold red]Error:[/bold red] FastAPI not installed. "
            "Install with: pip install pocket-recs[api]"
        )
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("version")
def show_version() -> None:
    """Show pocket-recs version."""
    from pocket_recs import __version__

    console.print(f"pocket-recs version {__version__}")


if __name__ == "__main__":
    app()

