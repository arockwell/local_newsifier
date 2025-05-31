# Documentation Strategy Knowledge Base

## Overview
This document outlines the comprehensive documentation strategy for the Local Newsifier project, consolidating knowledge about documentation needs, patterns, and best practices.

## Documentation Philosophy

### Core Principles
1. **Documentation as Code**: Keep docs close to implementation
2. **Real Examples**: Use actual code from the project, not hypothetical examples
3. **Progressive Disclosure**: Start simple, add complexity as needed
4. **Maintainability**: Automated where possible, manually curated where valuable

## Documentation Structure

### Project Documentation Hierarchy
```
/
├── README.md                 # Project overview and quick start
├── CLAUDE.md                # AI assistant instructions
├── AGENTS.md                # Directory of all CLAUDE.md files
└── docs/
    ├── README.md            # Documentation index
    ├── plans/               # Consolidated knowledge from issues
    │   ├── apify-integration.md
    │   ├── dependency-injection-architecture.md
    │   └── ...
    ├── architecture/        # System design documents
    │   ├── adr/            # Architecture Decision Records
    │   ├── diagrams/       # System diagrams
    │   └── patterns.md     # Design patterns used
    ├── guides/             # How-to guides
    │   ├── setup.md
    │   ├── development.md
    │   └── deployment.md
    ├── api/                # API documentation
    │   ├── rest-api.md
    │   └── webhooks.md
    └── reference/          # Technical reference
        ├── models.md
        ├── services.md
        └── cli.md
```

## Documentation Types

### 1. Architecture Decision Records (ADRs)
Document significant architectural decisions:

```markdown
# ADR-001: Migration from DIContainer to fastapi-injectable

## Status
Accepted

## Context
The custom DIContainer created hidden dependencies and testing difficulties...

## Decision
Migrate to fastapi-injectable for explicit dependency management...

## Consequences
- Positive: Better testability, explicit dependencies
- Negative: Migration effort required
```

### 2. Model Relationship Diagrams
Visual representation of database relationships:

```mermaid
erDiagram
    Article ||--o{ Entity : contains
    Article ||--o{ AnalysisResult : has
    Entity }o--|| CanonicalEntity : resolves_to
    ApifySourceConfig ||--o{ ApifyWebhookData : generates
```

### 3. Flow Diagrams
Document complex processes:

```mermaid
graph TD
    A[RSS Feed] --> B[Fetch Articles]
    B --> C[Extract Entities]
    C --> D[Resolve Canonical]
    D --> E[Analyze Sentiment]
    E --> F[Generate Trends]
```

### 4. API Documentation
Clear endpoint documentation with examples:

```markdown
## POST /webhooks/apify

Receives webhook notifications from Apify actors.

### Request
```json
{
  "actorId": "apify/web-scraper",
  "actorRunId": "run_123",
  "status": "SUCCEEDED"
}
```

### Response
```json
{
  "status": "accepted",
  "webhook_id": "webhook_456"
}
```
```

### 5. Code Examples
Real examples from the codebase:

```python
# From src/local_newsifier/di/providers.py
@injectable(use_cache=False)
def get_article_service(
    article_crud: Annotated[Any, Depends(get_article_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    """
    Provides ArticleService with configured dependencies.

    Example usage in endpoint:
        @router.get("/articles")
        def list_articles(
            service: Annotated[ArticleService, Depends(get_article_service)]
        ):
            return service.get_all()
    """
    from local_newsifier.services.article_service import ArticleService
    return ArticleService(
        article_crud=article_crud,
        session_factory=lambda: session
    )
```

## Documentation Standards

### 1. Docstring Format
Use Google-style docstrings:

```python
def process_article(article_id: int, analyze: bool = True) -> AnalysisResult:
    """Process an article through the analysis pipeline.

    Args:
        article_id: The ID of the article to process
        analyze: Whether to run sentiment analysis

    Returns:
        AnalysisResult containing entities and sentiment scores

    Raises:
        ArticleNotFoundError: If article doesn't exist
        AnalysisError: If analysis fails

    Example:
        result = process_article(123, analyze=True)
        print(f"Found {len(result.entities)} entities")
    """
```

### 2. README Structure
Each module should have a README:

```markdown
# Module Name

## Overview
Brief description of what this module does.

## Components
- `service.py`: Main service implementation
- `models.py`: Data models
- `utils.py`: Helper functions

## Usage
```python
from module import Service
service = Service()
result = service.process()
```

## Configuration
- `ENV_VAR`: Description (default: value)

## Testing
```bash
pytest tests/test_module.py
```
```

### 3. CLI Documentation
Document all CLI commands:

```markdown
## Command: nf feeds add

Add a new RSS feed to the system.

### Usage
```bash
nf feeds add <URL> [OPTIONS]
```

### Options
- `--name`: Feed name (default: extracted from URL)
- `--active/--inactive`: Set initial state (default: active)

### Examples
```bash
# Add a basic feed
nf feeds add https://example.com/rss

# Add with custom name
nf feeds add https://example.com/rss --name "Example News"

# Add as inactive
nf feeds add https://example.com/rss --inactive
```
```

## Documentation Tools

### 1. Mermaid Diagrams
For visual documentation in Markdown:

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant W as Worker
    participant D as Database

    U->>A: POST /articles
    A->>D: Save article
    A->>W: Queue processing
    A-->>U: 202 Accepted
    W->>D: Update analysis
```

### 2. OpenAPI/Swagger
Auto-generated from FastAPI:

```python
app = FastAPI(
    title="Local Newsifier API",
    description="News analysis and entity tracking system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

### 3. Database Schema Documentation
Generated from SQLModel:

```python
# Auto-generate schema docs
from sqlmodel import SQLModel
from docs.generator import generate_model_docs

for model in SQLModel.__subclasses__():
    generate_model_docs(model)
```

## Documentation Maintenance

### 1. Automated Checks
- Docstring coverage in CI
- Link validation
- Example code testing
- Diagram rendering validation

### 2. Review Process
- Documentation updates required for:
  - New features
  - API changes
  - Configuration changes
  - Breaking changes

### 3. Version Management
- Tag documentation with releases
- Maintain changelog
- Document migration guides

## Common Documentation Patterns

### 1. Configuration Documentation
```markdown
## Configuration

### Required Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://user:pass@host/db |
| APIFY_TOKEN | Apify API token | apify_api_xxxx |

### Optional Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| LOG_LEVEL | Logging level | INFO |
| WORKER_CONCURRENCY | Number of worker threads | 4 |
```

### 2. Error Documentation
```markdown
## Common Errors

### DatabaseConnectionError
**Cause**: Cannot connect to PostgreSQL
**Solution**:
1. Check DATABASE_URL is correct
2. Ensure PostgreSQL is running
3. Verify network connectivity

### ApifyAuthenticationError
**Cause**: Invalid or expired Apify token
**Solution**:
1. Verify APIFY_TOKEN is set
2. Check token permissions
3. Regenerate token if expired
```

### 3. Integration Guides
```markdown
## Apify Integration Guide

### Prerequisites
1. Apify account with API token
2. Webhook endpoint accessible from internet

### Setup Steps
1. Configure Apify token:
   ```bash
   export APIFY_TOKEN=your_token
   ```

2. Create actor configuration:
   ```bash
   nf apify config create \
     --name "News Crawler" \
     --actor-id "apify/web-scraper"
   ```

3. Set up webhook:
   ```bash
   nf apify config update 1 \
     --webhook-url "https://your-app.com/webhooks/apify"
   ```
```

## Documentation Quality Checklist

### For New Features
- [ ] Update relevant documentation
- [ ] Add code examples
- [ ] Update CLI help text
- [ ] Add to changelog
- [ ] Update diagrams if needed

### For API Changes
- [ ] Update OpenAPI spec
- [ ] Document breaking changes
- [ ] Provide migration guide
- [ ] Update client examples

### For Configuration Changes
- [ ] Document new variables
- [ ] Update example configs
- [ ] Note in deployment guide
- [ ] Update docker-compose if needed

## Future Documentation Improvements

### 1. Interactive Documentation
- Jupyter notebooks for tutorials
- Interactive API explorer
- Live code examples

### 2. Video Tutorials
- Setup walkthrough
- Feature demonstrations
- Architecture deep-dives

### 3. Automated Generation
- Model documentation from code
- API client generation
- Dependency graphs

### 4. Searchable Knowledge Base
- Full-text search
- Tag-based navigation
- AI-powered Q&A

## References

- [Documentation Best Practices](https://documentation.divio.com/)
- [Google Developer Documentation Style Guide](https://developers.google.com/style)
- Project Issues: #74, #156, #266, #378, #425, #478, #522, #541, #615
