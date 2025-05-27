"""CLI commands for testing the new background task system."""

import time

import click
import requests
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def test_background():
    """Test background task processing system."""
    pass


@test_background.command()
@click.argument("article_id", type=int)
@click.option("--api-url", default="http://localhost:8000", help="API base URL")
def process_article(article_id: int, api_url: str):
    """Test processing a single article via background task."""
    url = f"{api_url}/background-tasks/process-article/{article_id}"

    console.print(f"[yellow]Submitting article {article_id} for processing...[/yellow]")

    try:
        response = requests.post(url)
        response.raise_for_status()

        data = response.json()
        task_id = data["task_id"]

        console.print(f"[green]Task created: {task_id}[/green]")
        console.print(f"Status: {data['status']}")
        console.print(f"Message: {data['message']}")

        # Poll for completion
        console.print("\n[yellow]Polling for task completion...[/yellow]")
        _poll_task_status(api_url, task_id)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")


@test_background.command()
@click.option("--feed-urls", multiple=True, help="Feed URLs to process (can specify multiple)")
@click.option(
    "--process-articles/--no-process-articles",
    default=True,
    help="Whether to process articles after fetching",
)
@click.option("--api-url", default="http://localhost:8000", help="API base URL")
def fetch_feeds(feed_urls: tuple, process_articles: bool, api_url: str):
    """Test fetching RSS feeds via background task."""
    url = f"{api_url}/background-tasks/fetch-feeds"

    params = {"process_articles": process_articles}
    if feed_urls:
        params["feed_urls"] = list(feed_urls)

    console.print("[yellow]Submitting feeds for processing...[/yellow]")

    try:
        response = requests.post(url, json=params)
        response.raise_for_status()

        data = response.json()
        task_id = data["task_id"]

        console.print(f"[green]Task created: {task_id}[/green]")
        console.print(f"Status: {data['status']}")
        console.print(f"Message: {data['message']}")

        # Poll for completion
        console.print("\n[yellow]Polling for task completion...[/yellow]")
        _poll_task_status(api_url, task_id)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")


@test_background.command()
@click.option("--api-url", default="http://localhost:8000", help="API base URL")
def list_active(api_url: str):
    """List all active background tasks."""
    url = f"{api_url}/background-tasks/active"

    try:
        response = requests.get(url)
        response.raise_for_status()

        tasks = response.json()

        if not tasks:
            console.print("[yellow]No active tasks[/yellow]")
            return

        table = Table(title="Active Background Tasks")
        table.add_column("Task ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Created", style="yellow")
        table.add_column("Updated", style="yellow")

        for task in tasks:
            table.add_row(task["task_id"], task["status"], task["created_at"], task["updated_at"])

        console.print(table)

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")


@test_background.command()
@click.argument("task_id")
@click.option("--api-url", default="http://localhost:8000", help="API base URL")
def status(task_id: str, api_url: str):
    """Get status of a specific background task."""
    url = f"{api_url}/background-tasks/status/{task_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()

        task = response.json()

        console.print("\n[bold]Task Status[/bold]")
        console.print(f"Task ID: [cyan]{task['task_id']}[/cyan]")
        console.print(f"Status: [green]{task['status']}[/green]")
        console.print(f"Created: [yellow]{task['created_at']}[/yellow]")
        console.print(f"Updated: [yellow]{task['updated_at']}[/yellow]")

        if task.get("error"):
            console.print(f"Error: [red]{task['error']}[/red]")

        if task.get("result"):
            console.print("\n[bold]Result:[/bold]")
            console.print(task["result"])

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error: {e}[/red]")


def _poll_task_status(api_url: str, task_id: str, max_attempts: int = 30):
    """Poll task status until completion."""
    url = f"{api_url}/background-tasks/status/{task_id}"

    for attempt in range(max_attempts):
        try:
            response = requests.get(url)
            response.raise_for_status()

            task = response.json()
            status = task["status"]

            if status in ["completed", "failed"]:
                console.print(f"\n[bold]Task {status}![/bold]")

                if task.get("error"):
                    console.print(f"Error: [red]{task['error']}[/red]")

                if task.get("result"):
                    console.print("\n[bold]Result:[/bold]")
                    console.print(task["result"])

                return

            console.print(f"Status: {status} (attempt {attempt + 1}/{max_attempts})")
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            console.print(f"[red]Error polling status: {e}[/red]")
            return

    console.print("[yellow]Task did not complete within timeout[/yellow]")
