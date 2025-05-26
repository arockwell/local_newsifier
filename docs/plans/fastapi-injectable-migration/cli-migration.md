# CLI Migration from FastAPI-Injectable

This guide details how the CLI migration away from FastAPI-Injectable aligns with the CLI-to-HTTP architecture change.

## Overview

The CLI's current use of FastAPI-Injectable is the primary source of event loop conflicts. By migrating the CLI to use HTTP APIs instead of direct dependency injection, we eliminate these issues entirely.

## Current Problems

### 1. Event Loop Conflicts
```python
# Current problematic pattern in CLI
@cli.command()
def process_feed(
    feed_id: int,
    # This causes event loop issues outside FastAPI context
    feed_service: Annotated[RSSFeedService, Depends(get_feed_service)]
):
    # CLI runs in sync context but injectable expects async
    feed_service.process_feed(feed_id)
```

### 2. Complex Test Workarounds
```python
# Previous test complexity (NOW RESOLVED)
# The custom event_loop_fixture has been removed

# New approach using pytest-asyncio
@pytest.mark.asyncio
async def test_cli_command():
    # Tests now work consistently without workarounds
    result = await async_cli_function()
    assert result == expected
```

## Migration Strategy

### Phase 1: Create HTTP Client

Create a new HTTP client for CLI commands:

```python
# cli/client.py
import httpx
from typing import Optional, Dict, Any
from local_newsifier.config.settings import get_settings

class CLIClient:
    """HTTP client for CLI commands."""

    def __init__(self, base_url: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.api_base_url
        self.client = httpx.Client(base_url=self.base_url)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    # Article methods
    def list_articles(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        response = self.client.get("/articles", params={"skip": skip, "limit": limit})
        response.raise_for_status()
        return response.json()

    def create_article(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.post("/articles", json=article_data)
        response.raise_for_status()
        return response.json()

    def process_article(self, url: str) -> Dict[str, Any]:
        response = self.client.post("/articles/process", json={"url": url})
        response.raise_for_status()
        return response.json()

    # Feed methods
    def list_feeds(self) -> Dict[str, Any]:
        response = self.client.get("/feeds")
        response.raise_for_status()
        return response.json()

    def process_feed(self, feed_id: int) -> Dict[str, Any]:
        response = self.client.post(f"/feeds/{feed_id}/process")
        response.raise_for_status()
        return response.json()

    # Analysis methods
    def analyze_trends(self, params: Dict[str, Any]) -> Dict[str, Any]:
        response = self.client.post("/analysis/trends", json=params)
        response.raise_for_status()
        return response.json()
```

### Phase 2: Create Async Client Option

For commands that benefit from async operations:

```python
# cli/async_client.py
import httpx
import asyncio
from typing import Optional, Dict, Any, List

class AsyncCLIClient:
    """Async HTTP client for CLI commands."""

    def __init__(self, base_url: Optional[str] = None):
        settings = get_settings()
        self.base_url = base_url or settings.api_base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def process_multiple_articles(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Process multiple articles concurrently."""
        tasks = [
            self.client.post("/articles/process", json={"url": url})
            for url in urls
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for response in responses:
            if isinstance(response, Exception):
                results.append({"error": str(response)})
            else:
                response.raise_for_status()
                results.append(response.json())

        return results
```

### Phase 3: Update CLI Commands

Convert CLI commands to use the HTTP client:

```python
# cli/commands/articles.py
from typer import Typer
from rich.console import Console
from rich.table import Table

from local_newsifier.cli.client import CLIClient

app = Typer()
console = Console()

@app.command()
def list(skip: int = 0, limit: int = 100):
    """List articles."""
    with CLIClient() as client:
        try:
            articles = client.list_articles(skip=skip, limit=limit)

            # Display results
            table = Table(title="Articles")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="magenta")
            table.add_column("URL", style="green")

            for article in articles:
                table.add_row(
                    str(article["id"]),
                    article["title"],
                    article["url"]
                )

            console.print(table)

        except httpx.HTTPError as e:
            console.print(f"[red]Error: {e}[/red]")

@app.command()
def process(url: str):
    """Process a new article."""
    with CLIClient() as client:
        try:
            with console.status("[bold green]Processing article..."):
                result = client.process_article(url)

            console.print(f"[green]✓[/green] Article processed successfully!")
            console.print(f"ID: {result['id']}")
            console.print(f"Title: {result['title']}")
            console.print(f"Entities found: {len(result.get('entities', []))}")

        except httpx.HTTPError as e:
            console.print(f"[red]Error: {e}[/red]")
```

### Phase 4: Handle Long-Running Operations

For operations that take time, implement progress tracking:

```python
# cli/commands/feeds.py
import time
from rich.progress import Progress, SpinnerColumn, TextColumn

@app.command()
def process_feed(feed_id: int):
    """Process all articles from a feed."""
    with CLIClient() as client:
        try:
            # Start processing
            response = client.process_feed(feed_id)
            task_id = response["task_id"]

            # Poll for status
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                task = progress.add_task("Processing feed...", total=None)

                while True:
                    status = client.get_task_status(task_id)

                    if status["state"] == "PENDING":
                        progress.update(task, description="Waiting to start...")
                    elif status["state"] == "PROGRESS":
                        current = status.get("current", 0)
                        total = status.get("total", 100)
                        progress.update(
                            task,
                            description=f"Processing: {current}/{total}",
                            total=total,
                            completed=current
                        )
                    elif status["state"] == "SUCCESS":
                        progress.update(task, description="✓ Completed!")
                        break
                    elif status["state"] == "FAILURE":
                        console.print(f"[red]Task failed: {status.get('error')}[/red]")
                        break

                    time.sleep(1)

            # Show results
            if status["state"] == "SUCCESS":
                result = status["result"]
                console.print(f"\n[green]Feed processed successfully![/green]")
                console.print(f"Articles processed: {result['articles_processed']}")
                console.print(f"New articles: {result['new_articles']}")
                console.print(f"Updated articles: {result['updated_articles']}")

        except httpx.HTTPError as e:
            console.print(f"[red]Error: {e}[/red]")
```

### Phase 5: Local Development Mode

Support direct service calls for development/testing:

```python
# cli/client.py
class CLIClient:
    def __init__(self, base_url: Optional[str] = None, local_mode: bool = False):
        self.local_mode = local_mode
        if not local_mode:
            settings = get_settings()
            self.base_url = base_url or settings.api_base_url
            self.client = httpx.Client(base_url=self.base_url)

    def list_articles(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        if self.local_mode:
            # Direct service call for local development
            from local_newsifier.services.article_service import ArticleService
            from local_newsifier.database.engine import SessionLocal

            with SessionLocal() as session:
                service = ArticleService()
                articles = service.list_articles(session, skip=skip, limit=limit)
                return [article.dict() for article in articles]
        else:
            # HTTP call for production
            response = self.client.get("/articles", params={"skip": skip, "limit": limit})
            response.raise_for_status()
            return response.json()
```

## Benefits of CLI Migration

### 1. No Event Loop Issues
- CLI operates in pure sync context
- No async/sync boundary crossing
- No injectable framework complications

### 2. Simplified Testing
```python
# Simple test without event loop fixtures
def test_list_articles(mock_http_client):
    mock_http_client.get.return_value.json.return_value = [
        {"id": 1, "title": "Test Article"}
    ]

    result = runner.invoke(app, ["articles", "list"])
    assert result.exit_code == 0
    assert "Test Article" in result.output
```

### 3. Better Error Handling
```python
@app.command()
def process(url: str):
    """Process article with proper error handling."""
    with CLIClient() as client:
        try:
            result = client.process_article(url)
            console.print("[green]Success![/green]")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                console.print("[yellow]Article not found[/yellow]")
            elif e.response.status_code == 409:
                console.print("[yellow]Article already exists[/yellow]")
            else:
                console.print(f"[red]Server error: {e}[/red]")
        except httpx.RequestError as e:
            console.print(f"[red]Connection error: {e}[/red]")
```

### 4. Progress and Feedback
```python
from rich.progress import track

@app.command()
def batch_process(file_path: str):
    """Process multiple URLs from file."""
    with open(file_path) as f:
        urls = [line.strip() for line in f if line.strip()]

    with CLIClient() as client:
        results = {"success": 0, "failed": 0}

        for url in track(urls, description="Processing articles..."):
            try:
                client.process_article(url)
                results["success"] += 1
            except Exception as e:
                results["failed"] += 1
                console.print(f"[red]Failed: {url} - {e}[/red]")

        console.print(f"\n[green]Processed: {results['success']}[/green]")
        console.print(f"[red]Failed: {results['failed']}[/red]")
```

## Migration Timeline

1. **Week 1**: Create HTTP client and async client
2. **Week 2**: Migrate simple CRUD commands
3. **Week 3**: Migrate complex operations (feeds, analysis)
4. **Week 4**: Add progress tracking and error handling
5. **Week 5**: Update tests and documentation

## Testing Strategy

### 1. Unit Tests
```python
# test_cli_client.py
def test_cli_client_list_articles():
    with patch("httpx.Client") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get.return_value.json.return_value = [{"id": 1}]

        client = CLIClient()
        result = client.list_articles()

        assert result == [{"id": 1}]
        mock_client.get.assert_called_with("/articles", params={"skip": 0, "limit": 100})
```

### 2. Integration Tests
```python
# test_cli_integration.py
def test_article_command_integration(test_api_server):
    """Test against running API server."""
    result = runner.invoke(app, ["articles", "create", "--url", "http://example.com"])
    assert result.exit_code == 0
    assert "Article created" in result.output
```

### 3. End-to-End Tests
```python
# test_cli_e2e.py
def test_full_workflow():
    """Test complete workflow through CLI."""
    # Create article
    create_result = runner.invoke(app, ["articles", "create", "--url", "http://example.com"])
    assert create_result.exit_code == 0

    # List articles
    list_result = runner.invoke(app, ["articles", "list"])
    assert list_result.exit_code == 0
    assert "example.com" in list_result.output
```

## Migration Checklist

- [ ] Create HTTP client with all required methods
- [ ] Create async client for concurrent operations
- [ ] Update all CLI commands to use HTTP client
- [ ] Remove all `Depends()` imports from CLI
- [ ] Remove all injectable imports from CLI
- [ ] Add progress tracking for long operations
- [ ] Implement comprehensive error handling
- [ ] Update all CLI tests
- [x] Remove event_loop_fixture from CLI tests (COMPLETED)
- [ ] Update CLI documentation
- [ ] Test local development mode
- [ ] Performance test batch operations
