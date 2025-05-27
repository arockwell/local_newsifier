# Refactoring Plan

## Overview
Strategic refactoring to improve code quality, maintainability, and performance while aligning with the sync-only architecture.

## High Priority Refactoring Tasks

### 1. Service Layer Consolidation
**Current issues:**
- Duplicate logic between services
- Inconsistent error handling
- Mixed responsibilities

**Refactoring tasks:**
```python
# Before: Scattered logic
class ArticleService:
    def process_article(self, url):
        # Scraping logic here
        # Entity extraction here
        # Analysis here

# After: Single responsibility
class ArticleService:
    def __init__(self, scraper, entity_extractor, analyzer):
        self.scraper = scraper
        self.entity_extractor = entity_extractor
        self.analyzer = analyzer

    def process_article(self, url):
        content = self.scraper.scrape(url)
        entities = self.entity_extractor.extract(content)
        analysis = self.analyzer.analyze(content, entities)
        return self.save_results(content, entities, analysis)
```

### 2. Database Query Optimization
**Current issues:**
- N+1 query problems
- Missing indexes
- Inefficient joins

**Refactoring tasks:**
```python
# Before: N+1 queries
articles = session.query(Article).all()
for article in articles:
    entities = session.query(Entity).filter_by(article_id=article.id).all()

# After: Eager loading
articles = session.query(Article).options(
    selectinload(Article.entities),
    selectinload(Article.analysis_results)
).all()
```

### 3. Error Handling Standardization
**Current issues:**
- Inconsistent error types
- Missing error context
- Poor error messages

**Refactoring approach:**
```python
# Create domain-specific exceptions
class ArticleProcessingError(BaseError):
    def __init__(self, article_id: int, step: str, cause: Exception):
        self.article_id = article_id
        self.step = step
        super().__init__(
            f"Failed to process article {article_id} at step '{step}': {cause}"
        )

# Use context managers for consistent handling
@contextmanager
def handle_article_errors(article_id: int, step: str):
    try:
        yield
    except Exception as e:
        logger.error(f"Article {article_id} failed at {step}", exc_info=True)
        raise ArticleProcessingError(article_id, step, e)
```

### 4. Dependency Injection Cleanup
**Current issues:**
- Circular dependencies
- Runtime imports
- Complex provider chains

**Refactoring tasks:**
1. **Flatten provider hierarchy**
   ```python
   # Before: Deep nesting
   @injectable
   def get_article_service(
       crud: Annotated[Any, Depends(get_article_crud)],
       analyzer: Annotated[Any, Depends(get_analyzer)],
       extractor: Annotated[Any, Depends(get_extractor)]
   ):
       return ArticleService(crud, analyzer, extractor)

   # After: Direct injection
   @injectable
   def get_article_service(session: Session):
       return ArticleService(
           crud=ArticleCRUD(),
           analyzer=Analyzer(),
           extractor=Extractor(),
           session=session
       )
   ```

2. **Remove circular imports**
   - Move shared types to separate modules
   - Use TYPE_CHECKING for type hints
   - Lazy load dependencies

### 5. Model Relationships Optimization
**Current issues:**
- Expensive relationship loading
- Missing relationship constraints
- Inefficient cascades

**Refactoring tasks:**
```python
# Add proper relationship loading strategies
class Article(SQLModel, table=True):
    # Use lazy loading by default
    entities: List["Entity"] = Relationship(
        back_populates="article",
        sa_relationship_kwargs={"lazy": "select"}
    )

    # Add explicit loading methods
    def load_entities(self, session: Session):
        stmt = select(Entity).where(Entity.article_id == self.id)
        return session.exec(stmt).all()
```

### 6. Configuration Management
**Current issues:**
- Hardcoded values
- Environment variable chaos
- Missing validation

**Refactoring approach:**
```python
# Create structured configuration
from pydantic import BaseSettings, validator

class DatabaseConfig(BaseSettings):
    host: str
    port: int = 5432
    name: str
    user: str
    password: str

    @validator("port")
    def validate_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Invalid port number")
        return v

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class AppConfig(BaseSettings):
    database: DatabaseConfig
    api_timeout: int = 30
    max_retries: int = 3

    class Config:
        env_nested_delimiter = "__"
```

### 7. Test Infrastructure Improvement
**Current issues:**
- Slow test execution
- Flaky tests
- Poor test isolation

**Refactoring tasks:**
1. **Improve fixture efficiency**
   ```python
   # Use session-scoped fixtures for expensive resources
   @pytest.fixture(scope="session")
   def db_engine():
       engine = create_engine("sqlite:///:memory:")
       Base.metadata.create_all(engine)
       yield engine
       engine.dispose()
   ```

2. **Better test data factories**
   ```python
   class ArticleFactory:
       @staticmethod
       def create(session: Session, **kwargs):
           defaults = {
               "title": f"Test Article {uuid4()}",
               "url": f"https://example.com/{uuid4()}",
               "content": "Test content"
           }
           defaults.update(kwargs)
           article = Article(**defaults)
           session.add(article)
           session.commit()
           return article
   ```

### 8. API Response Standardization
**Current issues:**
- Inconsistent response formats
- Missing pagination
- Poor error responses

**Refactoring approach:**
```python
# Standardized response models
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class PaginatedResponse(APIResponse):
    data: List[Any]
    metadata: Dict[str, Any] = {
        "page": 1,
        "per_page": 20,
        "total": 0,
        "pages": 0
    }

# Consistent error handling
@app.exception_handler(ValidationError)
def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content=APIResponse(
            success=False,
            error="Validation failed",
            metadata={"errors": exc.errors()}
        ).dict()
    )
```

## Implementation Strategy
1. **Phase 1**: Error handling and configuration (Week 1-2)
2. **Phase 2**: Service layer consolidation (Week 3-4)
3. **Phase 3**: Database optimization (Week 5-6)
4. **Phase 4**: Test infrastructure (Week 7)
5. **Phase 5**: API standardization (Week 8)

## Success Metrics
- Reduced code duplication (target: -30%)
- Improved test execution time (target: -50%)
- Better error messages (100% coverage)
- Simplified dependency graph
- Consistent code patterns throughout

## Refactoring Rules
1. Always maintain backwards compatibility
2. Write tests before refactoring
3. Refactor in small, reviewable chunks
4. Document breaking changes
5. Measure performance impact
