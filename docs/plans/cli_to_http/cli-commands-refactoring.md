# CLI Commands Refactoring Plan

## Overview

This document details the refactoring of CLI commands to use the new HTTP client instead of direct dependency injection, providing a cleaner and more maintainable command structure.

## Command Structure

### Main CLI Group
```python
@click.group()
@click.option('--api-url', envvar='NEWSIFIER_API_URL', help='API base URL')
@click.option('--local', is_flag=True, help='Use local mode (no API server needed)')
@click.pass_context
def cli(ctx, api_url: Optional[str], local: bool):
    """Local Newsifier CLI - News processing and analysis tool."""
    ctx.ensure_object(dict)
    ctx.obj['client'] = NewsifierClient(base_url=api_url, local_mode=local)
```

## Commands Implementation

### 1. Process Command

**Purpose**: Process a single article

**Features**:
- URL validation
- Optional content pre-fetching
- Force refresh capability
- Rich console output with progress indicators
- Detailed result display

**Key Changes**:
- Uses HTTP client instead of direct service calls
- Handles API errors gracefully
- Provides better user feedback

### 2. Batch Command

**Purpose**: Process multiple articles from a file

**Features**:
- JSON file input support
- Configurable concurrency
- Async batch processing
- Progress tracking
- Result summary

**Implementation Highlights**:
```python
async def run_batch():
    async with AsyncNewsifierClient(base_url=client.base_url) as async_client:
        batch_result = await async_client.process_batch_async(urls, concurrent)
        task_id = batch_result['task_id']
        result = await async_client.wait_for_task(task_id)
        return result
```

### 3. Report Command

**Purpose**: Generate analysis reports

**Features**:
- Flexible date range selection
- Multiple output formats (JSON, HTML, PDF)
- File output option
- Console summary display

**Options**:
- `--days`: Look back N days
- `--start-date`: Specific start date
- `--end-date`: Specific end date
- `--format`: Output format selection
- `--output`: Save to file

### 4. Scrape Command

**Purpose**: Trigger news scraping

**Features**:
- Source selection
- Configurable time range
- Optional wait for completion
- Progress monitoring

**Interactive Elements**:
- Confirmation prompt for waiting
- Live progress updates
- Status polling

### 5. Health Command

**Purpose**: Check API status

**Features**:
- API connectivity check
- Database status verification
- Detailed error reporting
- Connection troubleshooting hints

## UI/UX Improvements

### Rich Console Integration

Using the `rich` library for enhanced output:

1. **Status Indicators**
   - Spinner animations for long operations
   - Progress bars where applicable
   - Color-coded status messages

2. **Tables**
   - Structured data display
   - Article summaries
   - Batch results

3. **Panels**
   - Health check results
   - Report summaries
   - Error details

### Error Handling

Consistent error presentation:
```python
try:
    result = client.operation()
except NewsifierAPIError as e:
    console.print(f"[red]❌ Error: {e.detail}[/red]")
    sys.exit(1)
except Exception as e:
    console.print(f"[red]❌ Unexpected error: {str(e)}[/red]")
    sys.exit(1)
```

## Migration Path

### Phase 1: Command Structure
1. Update click decorators
2. Add context passing
3. Initialize HTTP client

### Phase 2: Command Logic
1. Replace service calls with HTTP client calls
2. Update error handling
3. Add async support where needed

### Phase 3: Output Enhancement
1. Integrate rich console
2. Add progress indicators
3. Improve error messages

### Phase 4: Testing
1. Update command tests
2. Mock HTTP client
3. Test error scenarios

## Testing Strategy

### Unit Tests
```python
def test_process_command(cli_runner, mock_client):
    mock_client.process_article.return_value = {
        'id': 1,
        'title': 'Test Article',
        'status': 'processed'
    }

    result = cli_runner.invoke(cli, ['process', 'https://example.com'])
    assert result.exit_code == 0
    assert 'processed successfully' in result.output
```

### Integration Tests
- Test with real API
- Verify output formatting
- Check error handling

### User Acceptance Tests
- Command usability
- Error message clarity
- Performance perception

## Configuration

### Environment Variables
- `NEWSIFIER_API_URL`: API endpoint
- `NO_COLOR`: Disable colored output
- `NEWSIFIER_TIMEOUT`: Request timeout

### Configuration File
Support for `.newsifier.conf`:
```ini
[api]
url = http://localhost:8000
timeout = 30

[output]
format = rich
color = true
```

## Backward Compatibility

### Transition Period
- Support both old and new commands
- Deprecation warnings for old usage
- Migration guide for users

### Command Aliases
```python
# Support old command names
cli.add_command(process, name='process-article')  # Old name
cli.add_command(process, name='process')  # New name
```

## Documentation Updates

### Help Text
- Clear command descriptions
- Example usage for each command
- Option explanations

### User Guide
- Migration instructions
- New feature highlights
- Troubleshooting section

## Performance Considerations

### Connection Pooling
- Reuse HTTP connections
- Configurable pool size
- Connection timeout handling

### Async Operations
- Use async for batch operations
- Concurrent request limits
- Progress reporting

### Caching
- Optional response caching
- Cache invalidation commands
- Cache statistics
