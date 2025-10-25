"""Main entry point for the pi-ragbox CLI."""

import typer
from typing import Optional

app = typer.Typer(
    name="pi-ragbox",
    help="Pi-RagBox CLI tool for managing and interacting with your RAG system",
    add_completion=False,
)


@app.command()
def hello(name: Optional[str] = typer.Option(None, "--name", "-n", help="Name to greet")):
    """
    Placeholder command - greet someone.

    This is a placeholder command that will be replaced with actual functionality.
    """
    if name:
        typer.echo(f"Hello {name}!")
    else:
        typer.echo("Hello from pi-ragbox!")


@app.command()
def version():
    """Display the version of pi-ragbox."""
    from pi_ragbox import __version__
    typer.echo(f"pi-ragbox version: {__version__}")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
