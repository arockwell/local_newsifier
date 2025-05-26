# CLI HTTP Client Design

## Overview

This document outlines the design of the HTTP client that will replace direct dependency injection in the CLI, providing a clean interface for API communication.

## Architecture

### Client Classes

#### 1. NewsifierClient (Base Client)
Primary synchronous client for standard CLI operations.

**Key Features**:
- Synchronous methods for simple usage
- Error handling with custom exceptions
- Support for both local and remote modes
- Configurable timeout and base URL
- Context manager support

#### 2. AsyncNewsifierClient
Async-enabled client for advanced operations like batch processing.

**Key Features**:
- Async/await support
- Concurrent request handling
- Async context manager
- Task polling capabilities

### Error Handling

#### Custom Exception
```python
class NewsifierAPIError(Exception):
    """Custom exception for API errors"""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
```

#### Error Processing
- Extract error details from response
- Provide meaningful error messages
- Preserve HTTP status codes
- Handle connection errors gracefully

## Client Methods

### Core Operations

#### 1. process_article()
```python
def process_article(
    self,
    url: str,
    content: Optional[str] = None,
    force_refresh: bool = False
) -> Dict[str, Any]
```
Process a single article with optional content.

#### 2. generate_report()
```python
def generate_report(
    self,
    start_date: str,
    end_date: str,
    include_opinions: bool = True,
    output_format: str = "json"
) -> Dict[str, Any]
```
Generate reports for date ranges.

#### 3. run_scraper()
```python
def run_scraper(
    self,
    source: str = "all",
    days_back: int = 7
) -> Dict[str, Any]
```
Trigger news scraping operations.

#### 4. check_task_status()
```python
def check_task_status(self, task_id: str) -> Dict[str, Any]
```
Check status of background tasks.

#### 5. health_check()
```python
def health_check(self) -> Dict[str, Any]
```
Verify API connectivity.

### Async Operations

#### 1. process_batch_async()
```python
async def process_batch_async(
    self,
    urls: List[str],
    concurrent_limit: int = 5
) -> Dict[str, Any]
```
Process multiple articles concurrently.

#### 2. wait_for_task()
```python
async def wait_for_task(
    self,
    task_id: str,
    poll_interval: float = 2.0
) -> Dict[str, Any]
```
Poll for task completion.

## Configuration

### Environment Variables
- `NEWSIFIER_API_URL`: Base URL for API
- Default: `http://localhost:8000`

### Client Options
- `base_url`: API endpoint base
- `timeout`: Request timeout (default: 30s)
- `local_mode`: Use TestClient instead of HTTP

## Local Mode

Special mode for testing without running API server:
- Uses FastAPI TestClient internally
- Direct function calls instead of HTTP
- Useful for unit tests and development
- No async support in local mode

## Usage Examples

### Basic Usage
```python
with NewsifierClient() as client:
    result = client.process_article("https://example.com/article")
    print(f"Processed article ID: {result['id']}")
```

### Async Batch Processing
```python
async with AsyncNewsifierClient() as client:
    result = await client.process_batch_async(urls, concurrent_limit=10)
    final_result = await client.wait_for_task(result['task_id'])
```

### Error Handling
```python
try:
    result = client.generate_report(start_date, end_date)
except NewsifierAPIError as e:
    if e.status_code == 404:
        print("Resource not found")
    else:
        print(f"API Error: {e.detail}")
```

## Testing Strategy

### Unit Tests
- Mock httpx responses
- Test error scenarios
- Verify request construction

### Integration Tests
- Test against real API
- Verify timeout handling
- Test connection failures

### Local Mode Tests
- Use TestClient directly
- No network calls
- Fast execution
