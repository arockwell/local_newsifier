# CLI Router Implementation Plan

## Overview

This document details the implementation of FastAPI router endpoints that will serve as the backend for CLI operations.

## Router Structure

### Location
- **File**: `src/local_newsifier/api/routers/cli.py`
- **Prefix**: `/cli`
- **Tags**: `["CLI Operations"]`

## Endpoints

### 1. Article Processing

#### POST `/cli/articles/process`
Process a single article with optional content and force refresh.

**Request Model**:
```python
class ProcessArticleRequest(BaseModel):
    url: str = Field(..., description="URL of the article to process")
    content: Optional[str] = Field(None, description="Pre-fetched article content")
    force_refresh: bool = Field(False, description="Force re-processing even if exists")
```

**Response Model**:
```python
class ProcessArticleResponse(BaseModel):
    id: int
    title: str
    url: str
    opinion_count: int
    processing_time: float
    status: str
    message: Optional[str] = None
```

**Features**:
- Checks for existing articles
- Supports force refresh
- Background entity extraction
- Timing metrics

### 2. Batch Processing

#### POST `/cli/articles/batch`
Process multiple articles concurrently.

**Request Model**:
```python
class BatchProcessRequest(BaseModel):
    urls: List[str] = Field(..., description="List of URLs to process")
    concurrent_limit: int = Field(5, description="Max concurrent processing")
```

**Features**:
- Queues as background task
- Returns task ID for tracking
- Configurable concurrency

### 3. Report Generation

#### POST `/cli/reports/generate`
Generate reports for specified date ranges.

**Request Model**:
```python
class GenerateReportRequest(BaseModel):
    start_date: date
    end_date: date
    include_opinions: bool = True
    include_statistics: bool = True
    output_format: str = Field("json", regex="^(json|html|pdf)$")
```

**Features**:
- Multiple output formats
- Configurable content
- File download support for PDF

### 4. Task Status

#### GET `/cli/tasks/{task_id}/status`
Check status of long-running tasks.

**Response Model**:
```python
class TaskStatusResponse(BaseModel):
    task_id: str
    status: str = Field(..., regex="^(pending|processing|completed|failed)$")
    progress: Optional[int] = Field(None, ge=0, le=100)
    result: Optional[Any] = None
    error: Optional[str] = None
```

### 5. Scraper Control

#### POST `/cli/scraper/run`
Trigger news scraping operations.

**Parameters**:
- `source`: Target source (all|gvnews|infogainesville)
- `days_back`: Number of days to scrape (1-30)

### 6. Health Check

#### GET `/cli/health`
Verify API and database connectivity.

**Response**:
```json
{
    "status": "healthy",
    "database": "connected",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

## Implementation Guidelines

### Error Handling
- Use appropriate HTTP status codes
- Return detailed error messages in development
- Log errors for monitoring

### Background Tasks
- Use FastAPI's BackgroundTasks for long operations
- Implement task tracking system
- Provide progress updates where possible

### Database Sessions
- Use dependency injection for sessions
- Ensure proper session cleanup
- Handle transaction boundaries

### Security Considerations
- Validate all inputs
- Implement rate limiting for expensive operations
- Add authentication for production deployment

## Testing Strategy

### Unit Tests
- Mock database operations
- Test error scenarios
- Verify response models

### Integration Tests
- Use TestClient
- Test full request/response cycle
- Verify background task execution

### Performance Tests
- Measure endpoint response times
- Test concurrent request handling
- Monitor memory usage
