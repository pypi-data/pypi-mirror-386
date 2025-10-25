"""Main entry point for the pi-ragbox CLI."""

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import importlib.util

from .auth import login_flow
from .api import APIClient, AuthenticationError, APIError
from .config import (
    clear_credentials,
    load_credentials,
    get_default_project,
    save_default_project,
    set_config_option,
    get_config_option,
)

app = typer.Typer(
    name="pi-ragbox",
    help="Pi-RagBox CLI tool for managing and interacting with your RAG system",
    add_completion=False,
)

console = Console()


@app.command()
def login():
    """
    Authenticate with pi-ragbox.

    Opens a browser window for Google OAuth authentication and stores
    credentials locally for future API calls.
    """
    with console.status("[bold green]Starting authentication flow..."):
        pass

    success, message = login_flow()

    if success:
        rprint(f"[bold green]✓[/bold green] {message}")
        rprint("\n[dim]You can now run 'pi-ragbox init ~/ragbox' to initialize a new workspace.[/dim]")
    else:
        rprint(f"[bold red]✗[/bold red] {message}")
        raise typer.Exit(code=1)


@app.command()
def logout():
    """
    Remove stored authentication credentials.
    """
    clear_credentials()
    rprint("[bold green]✓[/bold green] Successfully logged out")


@app.command()
def projects():
    """
    List all projects for the authenticated user.
    """
    try:
        client = APIClient()
        projects_list = client.get_projects()

        if not projects_list:
            rprint("[yellow]No projects found.[/yellow]")
            return

        # Create a table for displaying projects
        table = Table(title="Your Projects", show_header=True, header_style="bold cyan")
        table.add_column("Project ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Corpus IDs", style="dim")

        for project in projects_list:
            corpus_ids = ", ".join(project.get("corpusIds", [])) if project.get("corpusIds") else "None"
            table.add_row(
                project.get("id", "N/A"),
                project.get("name", "Unnamed"),
                corpus_ids
            )

        console.print(table)

    except AuthenticationError as e:
        rprint(f"[bold red]✗[/bold red] {str(e)}")
        rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except APIError as e:
        rprint(f"[bold red]✗[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def whoami():
    """
    Display information about the currently authenticated user.
    """
    creds = load_credentials()

    if not creds:
        rprint("[yellow]Not logged in.[/yellow]")
        rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
        raise typer.Exit(code=1)

    rprint(f"[bold]Logged in as:[/bold] {creds.get('user_email', 'Unknown')}")

    if "expires_at" in creds:
        import datetime
        expiry = datetime.datetime.fromtimestamp(creds["expires_at"])
        rprint(f"[dim]Token expires:[/dim] {expiry.strftime('%Y-%m-%d %H:%M:%S')}")


@app.command()
def version():
    """Display the version of pi-ragbox."""
    from pi_ragbox import __version__
    typer.echo(f"pi-ragbox version: {__version__}")


@app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to set for the configuration key")
):
    """
    Set a configuration option.

    Example:
        pi-ragbox set my_option my_value
    """
    try:
        set_config_option(key, value)
        rprint(f"[bold green]✓[/bold green] Set [cyan]{key}[/cyan] = [bold]{value}[/bold]")

    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Failed to set config: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def get(
    key: str = typer.Argument(..., help="Configuration key to retrieve")
):
    """
    Get a configuration option value.

    Example:
        pi-ragbox get my_option
    """
    value = get_config_option(key)

    if value is not None:
        rprint(f"[cyan]{key}[/cyan] = [bold]{value}[/bold]")
    else:
        rprint(f"[yellow]{key}[/yellow] is not set")
        raise typer.Exit(code=1)


@app.command(name="set-project")
def set_project():
    """
    Change the default project for your pi-ragbox session.

    Lists all available projects and prompts you to select a new default.
    """
    try:
        # Get current credentials
        creds = load_credentials()
        if not creds:
            rprint("[bold red]✗[/bold red] Not logged in")
            rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
            raise typer.Exit(code=1)

        # Fetch projects
        client = APIClient()
        projects = client.get_projects()

        if not projects:
            rprint("[yellow]No projects found.[/yellow]")
            raise typer.Exit(code=0)

        # Display current default
        current_default = get_default_project()
        if current_default:
            rprint(f"[dim]Current default project:[/dim] [cyan]{current_default}[/cyan]\n")

        # Create a table for displaying projects
        table = Table(title="Available Projects", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Project Name", style="bold")
        table.add_column("Project ID", style="dim")

        for idx, project in enumerate(projects, 1):
            project_name = project.get("name", "Unnamed")
            project_id = project.get("id", "N/A")

            # Highlight current default
            if project_id == current_default:
                project_name = f"→ {project_name}"

            table.add_row(str(idx), project_name, project_id)

        console.print(table)
        rprint()

        # Prompt for selection
        while True:
            try:
                choice = typer.prompt("Enter project number", type=int)

                if 1 <= choice <= len(projects):
                    selected_project = projects[choice - 1]
                    project_id = selected_project["id"]
                    project_name = selected_project.get("name", "Unnamed")

                    save_default_project(project_id)
                    rprint(f"\n[bold green]✓[/bold green] Default project set to: [bold]{project_name}[/bold]")
                    rprint(f"[dim]  Project ID:[/dim] {project_id}")
                    break
                else:
                    rprint(f"[bold red]✗[/bold red] Please enter a number between 1 and {len(projects)}")

            except typer.Abort:
                rprint("\n[yellow]Cancelled.[/yellow]")
                raise typer.Exit(code=0)
            except ValueError:
                rprint("[bold red]✗[/bold red] Please enter a valid number")

    except AuthenticationError:
        rprint("[bold red]✗[/bold red] Authentication failed")
        rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except APIError as e:
        rprint(f"[bold red]✗[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def init(
    path: str = typer.Argument(..., help="Path where the Ragbox workspace will be created")
):
    """
    Initialize a new Ragbox workspace with starter flow templates.

    Creates a pi_flows directory with template files that you can customize
    and deploy to Modal.

    Example:
        pi-ragbox init ~/my-ragbox-flows
    """
    # Find the installed search_service package
    spec = importlib.util.find_spec("search_service")
    if not spec or not spec.origin:
        rprint("[bold red]✗[/bold red] Could not find search_service package")
        rprint("\n[dim]Please ensure search-service is installed.[/dim]")
        raise typer.Exit(code=1)

    # Expand and resolve the target path
    target_path = Path(path).expanduser().resolve()
    pi_flows_dir = target_path / "pi_flows"

    # Check if pi_flows already exists
    if pi_flows_dir.exists():
        rprint(f"[bold yellow]⚠[/bold yellow] Directory already exists: {pi_flows_dir}")
        confirm = typer.confirm("Do you want to overwrite it?", default=False)
        if not confirm:
            rprint("[dim]Cancelled.[/dim]")
            raise typer.Exit(code=0)

    # Find the builtin_flows directory in the installed package
    package_path = Path(spec.origin).parent
    source_dir = package_path / "builtin_flows" / "pi_flows"

    if not source_dir.exists():
        rprint(f"[bold red]✗[/bold red] Source directory not found: {source_dir}")
        rprint("\n[dim]Please ensure search-service is properly installed.[/dim]")
        raise typer.Exit(code=1)

    # Files to copy
    files_to_copy = ["__init__.py", "search_simple.py", "requirements.txt"]

    for file_name in files_to_copy:
        source_file = source_dir / file_name
        if not source_file.exists():
            rprint(f"[bold red]✗[/bold red] Source file not found: {source_file}")
            raise typer.Exit(code=1)

    # Create the directory structure
    try:
        pi_flows_dir.mkdir(parents=True, exist_ok=True)
        rprint(f"[bold green]✓[/bold green] Created directory: {pi_flows_dir}")
    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Failed to create directory: {str(e)}")
        raise typer.Exit(code=1)

    # Copy the template files
    try:
        for file_name in files_to_copy:
            source_file = source_dir / file_name
            dest_file = pi_flows_dir / file_name
            shutil.copy2(source_file, dest_file)
            rprint(f"[bold green]✓[/bold green] Copied {file_name}")

    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Failed to copy files: {str(e)}")
        raise typer.Exit(code=1)

    # Display success message with next steps
    rprint()
    success_panel = Panel(
        f"[bold green]Initialized Ragbox workspace at:[/bold green]\n"
        f"[cyan]{target_path}[/cyan]\n\n"
        f"[bold]Created structure:[/bold]\n"
        f"  {target_path}/\n"
        f"  └── pi_flows/\n"
        f"      ├── __init__.py\n"
        f"      └── requirements.txt\n"
        f"      └── search_simple.py\n\n"
        f"[bold]Next steps:[/bold]\n"
        f"  1. Review and customize your flow in pi_flows/search_simple.py\n"
        f"  2. (if needed) Add package dependencies to pi_flows/requirements.txt\n"
        f"  3. Deploy to Modal:\n"
        f"     [cyan]pi-ragbox serve hello-world {target_path}[/cyan]",
        title="[bold green]Workspace Initialized[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(success_panel)


@app.command()
def serve(
    app_id: str = typer.Argument(..., help="The application ID to use for this Modal stack"),
    python_path: str = typer.Argument(..., help="Path to prepend to PYTHONPATH for custom pi_flows")
):
    """
    Launch a Modal stack with custom configuration.

    This command deploys the search service to Modal with a custom application ID
    and custom Python flows directory.

    Example:
        pi-ragbox serve my-app-123 /path/to/custom/flows
    """
    # Check for default project and validate it exists
    default_project_id = get_default_project()
    if not default_project_id:
        rprint("[bold red]✗[/bold red] No default project configured")
        rprint("\n[dim]Please run 'pi-ragbox login' to authenticate and select a default project.[/dim]")
        raise typer.Exit(code=1)

    # Validate the project exists
    try:
        client = APIClient()
        projects = client.get_projects()

        project_exists = any(p.get("id") == default_project_id for p in projects)

        if not project_exists:
            rprint(f"[bold red]✗[/bold red] Default project '{default_project_id}' not found")
            rprint("\n[dim]Available projects:[/dim]")
            for project in projects:
                rprint(f"  • {project.get('name', 'Unnamed')} (ID: {project.get('id', 'N/A')})")
            rprint("\n[dim]Run 'pi-ragbox set-project' to change your default project.[/dim]")
            raise typer.Exit(code=1)

    except AuthenticationError:
        rprint("[bold red]✗[/bold red] Not authenticated")
        rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except APIError as e:
        rprint(f"[bold red]✗[/bold red] Failed to validate project: {str(e)}")
        raise typer.Exit(code=1)

    # Verify search_service package is available
    spec = importlib.util.find_spec("search_service")
    if not spec or not spec.origin:
        rprint("[bold red]✗[/bold red] Could not find search_service package")
        rprint("\n[dim]Please ensure search-service is installed.[/dim]")
        raise typer.Exit(code=1)
    
    working_dir = Path.cwd()

    # Validate python_path exists
    python_path_obj = Path(python_path)
    if not python_path_obj.exists():
        rprint(f"[bold red]✗[/bold red] Python path does not exist: {python_path}")
        raise typer.Exit(code=1)

    # Prepare environment variables
    env = os.environ.copy()

    # Prepend python_path to PYTHONPATH
    existing_pythonpath = env.get("PYTHONPATH", "")
    if existing_pythonpath:
        env["PYTHONPATH"] = f"{python_path}:{existing_pythonpath}"
    else:
        env["PYTHONPATH"] = python_path

    # Set the PI_APP_ID
    env["PI_APP_ID"] = app_id

    # Build the command
    command = ["modal", "serve", "--env=ragbox", "-m", "search_service.modal_main"]

    # Construct the application URL
    modal_url = f"https://pilabs-ragbox--{app_id}-fastapi-app-dev.modal.run"
    app_url = f"https://ragbox.withpi.ai/project/{default_project_id}?dev={modal_url}"

    # Display what we're doing
    rprint(f"[bold cyan]→[/bold cyan] Launching Modal stack for app ID: [bold]{app_id}[/bold]")
    rprint(f"[dim]  Project:[/dim] {default_project_id}")
    rprint(f"[dim]  Working directory:[/dim] {working_dir}")
    rprint(f"[dim]  Python path:[/dim] {python_path}")
    rprint(f"[dim]  Command:[/dim] {' '.join(command)}")
    rprint()

    # Display the application URL prominently
    url_panel = Panel(
        f"[bold cyan]{app_url}[/bold cyan]\n\n[dim]Opening in browser...[/dim]",
        title="[bold green]Your Application URL[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(url_panel)
    rprint()

    # Open browser
    try:
        webbrowser.open(app_url)
    except Exception as e:
        rprint(f"[yellow]⚠[/yellow] Could not open browser: {str(e)}")
        rprint("[dim]Please open the URL manually.[/dim]\n")

    try:
        # Run the subprocess
        result = subprocess.run(
            command,
            cwd=str(working_dir),
            env=env,
            capture_output=False,  # Stream output directly to terminal
            text=True
        )

        if result.returncode == 0:
            return
        else:
            raise typer.Exit(code=result.returncode)

    except FileNotFoundError:
        rprint("[bold red]✗[/bold red] Could not find 'uv' command")
        rprint("\n[dim]Please ensure uv is installed and available in your PATH[/dim]")
        raise typer.Exit(code=1)
    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Unexpected error: {str(e)}")
        raise typer.Exit(code=1)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
