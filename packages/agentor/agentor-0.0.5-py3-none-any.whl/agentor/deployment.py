import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from typing_extensions import Annotated

from agentor.sdk.client import CelestoSDK

app = typer.Typer(help="Agentor CLI - Deploy and manage AI agents")
console = Console()


def _get_api_key(api_key: Optional[str] = None) -> str:
    """Get API key from argument or environment variable."""
    final_api_key = api_key or os.environ.get("CELESTO_API_KEY")
    if not final_api_key:
        console.print("❌ [bold red]Error:[/bold red] API key not found.")
        console.print(
            "Please provide it via [bold]--api-key[/bold] or set [bold]CELESTO_API_KEY[/bold] environment variable."
        )
        console.print("\n[bold cyan]To get your API key:[/bold cyan]")
        console.print("1. Log in to https://celesto.ai")
        console.print("2. Navigate to Settings → Security")
        console.print("3. Copy your API key")
        raise typer.Exit(1)
    return final_api_key


@app.command()
def deploy(
    folder: Annotated[
        str,
        typer.Argument(
            ...,
            help="Path to the folder containing your agent code",
            default_factory=lambda: os.getcwd(),
        ),
    ],
    name: Annotated[
        str,
        typer.Option(
            ...,
            "--name",
            "-n",
            help="Name for your deployment",
            default_factory=lambda: f"my-agent-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        ),
    ],
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Description of your agent"
    ),
    envs: Optional[str] = typer.Option(
        None,
        "--envs",
        "-e",
        help='Environment variables as comma-separated key=value pairs (e.g., "API_KEY=xyz,DEBUG=true")',
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        "-k",
        help="Celesto API key (or set CELESTO_API_KEY env var)",
    ),
):
    """Deploy an agent to Celesto."""
    # Get API key
    final_api_key = _get_api_key(api_key)

    # Parse environment variables
    env_dict = {}
    if envs:
        for pair in envs.split(","):
            pair = pair.strip()
            if "=" not in pair:
                console.print(
                    f"❌ [bold red]Error:[/bold red] Invalid env pair: '{pair}'. Expected format: key=value"
                )
                raise typer.Exit(1)
            key, value = pair.split("=", 1)
            env_dict[key.strip()] = value.strip()

    # Validate folder path
    folder_path = Path(folder).resolve()
    if not folder_path.exists():
        console.print(
            f"❌ [bold red]Error:[/bold red] Folder '{folder_path}' does not exist."
        )
        raise typer.Exit(1)
    if not folder_path.is_dir():
        console.print(
            f"❌ [bold red]Error:[/bold red] '{folder_path}' is not a directory."
        )
        raise typer.Exit(1)

    # Deploy
    try:
        console.print(
            f"🚀 [bold cyan]Deploying[/bold cyan] '{name}' from {folder_path}..."
        )
        client = CelestoSDK(final_api_key)
        result = client.deployment.deploy(
            folder=folder_path, name=name, description=description, envs=env_dict
        )
        console.print("✅ [bold green]Deployment successful![/bold green]")

        # Show deployment details
        deployment_id = result.get("id")
        status = result.get("status")
        console.print(f"\n[bold]Deployment ID:[/bold] {deployment_id}")
        console.print(f"[bold]Status:[/bold] {status}")

        # Show URL once ready
        if status == "READY":
            cloud_url = f"https://api.celesto.ai/v1/deploy/apps/{deployment_id}/chat"
            console.print(f"[bold]URL:[/bold] [link={cloud_url}]{cloud_url}[/link]")
        else:
            console.print(
                "[yellow]⏳ Building... Run 'agentor ls' to check status[/yellow]"
            )

    except Exception as e:
        console.print(f"❌ [bold red]Deployment failed:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def list(
    api_key: Optional[str] = typer.Option(
        None, "--api-key", "-k", help="Celesto API key (or set CELESTO_API_KEY env var)"
    ),
):
    """List all deployments."""
    from rich.table import Table

    # Get API key
    final_api_key = _get_api_key(api_key)

    # List deployments
    try:
        client = CelestoSDK(final_api_key)
        deployments = client.deployment.list()

        if not deployments:
            console.print("📭 [yellow]No deployments found.[/yellow]")
            return

        # Create a table
        table = Table(
            title="🚀 Deployments", show_header=True, header_style="bold cyan"
        )
        table.add_column("Name", style="green")
        table.add_column("ID", style="dim")
        table.add_column("Status", style="cyan")
        table.add_column("Created At", style="magenta")
        table.add_column("URL", style="blue")

        for deployment in deployments:
            # Construct the cloud URL
            deployment_id = deployment.get("id", "N/A")
            if deployment_id != "N/A" and deployment.get("status") == "READY":
                cloud_url = (
                    f"https://api.celesto.ai/v1/deploy/apps/{deployment_id}/chat"
                )
            else:
                cloud_url = "Pending"

            table.add_row(
                deployment.get("name", "N/A"),
                deployment_id[:8] + "..."
                if deployment_id != "N/A"
                else "N/A",  # Shorten ID
                deployment.get("status", "N/A"),
                deployment.get("created_at", "N/A").split("T")[0]
                if deployment.get("created_at")
                else "N/A",  # Just date
                cloud_url,
            )

        console.print(table)
        console.print(f"\n📊 Total deployments: [bold]{len(deployments)}[/bold]")

    except Exception as e:
        console.print(f"❌ [bold red]Failed to list deployments:[/bold red] {e}")
        raise typer.Exit(1)


def main():
    """CLI entrypoint."""
    app()


if __name__ == "__main__":
    app()
