# Local Newsifier Architecture Overview

## System Architecture

Local Newsifier is a news article analysis system built with modern Python technologies, focusing on entity tracking, sentiment analysis, and headline trend detection.

## Core Technologies

- **Web Framework**: FastAPI
- **Database**: PostgreSQL with SQLModel ORM
- **Dependency Injection**: Native FastAPI DI
- **Background Tasks**: FastAPI BackgroundTasks
- **External Integrations**: Apify (web scraping), RSS feeds
- **NLP**: spaCy for entity recognition
- **Deployment**: Railway (single web process)

## Architecture Decisions

### 1. Sync-Only Implementation

The entire codebase uses synchronous patterns for simplicity and reliability:
- All database operations are synchronous
- All API endpoints use `def` (not `async def`)
- No async/await patterns anywhere
- Better debugging and error handling

### 2. Dependency Injection

- **API Layer**: Uses FastAPI's native dependency injection
- **CLI Layer**: Being migrated to HTTP client (no direct DI)
- Clean separation of concerns
- Easy testing with dependency overrides

### 3. Database Design

- **ORM**: SQLModel (combines SQLAlchemy + Pydantic)
- **Session Management**: Request-scoped sessions
- **Pattern**: Return IDs, not objects across boundaries
- **Migrations**: Alembic for schema management

### 4. Background Processing

- **Solution**: FastAPI BackgroundTasks
- **No Celery**: Simplified deployment, fewer dependencies
- **Use Cases**: Article processing, webhook handling
- **Pattern**: Fire-and-forget for non-critical tasks

## Data Flow

### Article Processing Pipeline

```
1. Content Acquisition
   ├── RSS Feed Polling
   └── Apify Web Scraping

2. Article Storage
   └── Deduplication by URL

3. Entity Extraction
   ├── NLP Processing (spaCy)
   └── Entity Resolution

4. Analysis
   ├── Sentiment Analysis
   ├── Trend Detection
   └── Relationship Mapping

5. Results
   ├── Database Storage
   └── API Access
```

## Component Architecture

### API Layer (`src/local_newsifier/api/`)
- FastAPI application
- RESTful endpoints
- Native dependency injection
- Webhook handlers
- Background task scheduling

### Service Layer (`src/local_newsifier/services/`)
- Business logic coordination
- Transaction management
- External API integration
- Data transformation

### CRUD Layer (`src/local_newsifier/crud/`)
- Database operations
- Query building
- Basic CRUD operations
- No business logic

### Models (`src/local_newsifier/models/`)
- SQLModel definitions
- Pydantic validation
- Database schema
- Response models

### Tools (`src/local_newsifier/tools/`)
- NLP processing
- Web scraping
- Sentiment analysis
- Entity resolution

### CLI (`src/local_newsifier/cli/`)
- Command-line interface
- Being migrated to HTTP client
- Administrative tasks
- Data management

## Integration Points

### Apify Integration
- Webhook endpoint for actor notifications
- Automatic article creation from datasets
- Configurable scraping sources
- Schedule management

### RSS Feed Processing
- Periodic feed polling
- Article deduplication
- Content extraction
- Metadata parsing

## Deployment Architecture

### Single Process Model
- One web process handles everything
- No separate worker processes
- No message broker (Redis/RabbitMQ)
- Simplified deployment and monitoring

### Environment Configuration
- PostgreSQL database (Railway provided)
- Environment-based configuration
- Secrets management via environment variables
- No complex orchestration

## Testing Architecture

### Test Organization
- Unit tests per component
- Integration tests for workflows
- API tests using TestClient
- Mock external dependencies

### Testing Patterns
- FastAPI native testing
- Dependency override for mocking
- In-memory SQLite for tests
- Parallel test execution

## Security Considerations

- API authentication (when needed)
- Webhook signature validation
- Environment variable secrets
- Input validation via Pydantic
- SQL injection prevention via ORM

## Performance Characteristics

- Synchronous processing (predictable)
- Connection pooling for database
- Efficient entity resolution
- Batch processing capabilities
- Caching where appropriate

## Future Architecture Considerations

### CLI to API Migration
- CLI becomes thin HTTP client
- All business logic in API
- Better separation of concerns
- Unified testing approach

### Potential Enhancements
- API rate limiting
- Result caching layer
- Batch processing API
- WebSocket for real-time updates
- Multi-tenant support

## Key Principles

1. **Simplicity First**: Sync-only, single process
2. **Clear Boundaries**: Well-defined layers
3. **Testability**: Dependency injection throughout
4. **Maintainability**: Clear code organization
5. **Scalability**: Horizontal scaling when needed
