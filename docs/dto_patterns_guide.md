# DTO Patterns Guide

## Philosophy: SQLModel-First Approach

Local Newsifier uses **SQLModel**, which was specifically designed to eliminate the need for separate DTOs by serving as both ORM models and Pydantic schemas. This guide explains when to use SQLModel alone versus when additional DTOs provide genuine value.

## Core Principle: Solve Real Problems, Not Theoretical Completeness

**Before creating any DTO, ask:**
1. Does SQLModel alone solve this problem?
2. Is there a concrete issue with type safety, validation, or API consistency?
3. Will this DTO be maintained and actually used?

## DTO Decision Matrix

### ✅ **High-Value DTOs (Create These)**

#### **1. Read DTOs** 
**Problem:** Session-bound SQLModel instances can't cross service boundaries
**Solution:** `<Model>Read` DTOs (already implemented)
```python
class ArticleRead(SQLModel):  # ✅ Essential
    id: int
    title: str
    # ... excludes relationships, includes related IDs
```

#### **2. List Response DTOs**
**Problem:** Inconsistent pagination across endpoints
**Solution:** Generic paginated response wrapper
```python
class ListResponse[T](SQLModel, Generic[T]):  # ✅ High value
    items: List[T]
    total: int
    page: int = 1
    size: int = 50
    has_next: bool
    has_prev: bool
```

#### **3. Domain Operation Result DTOs**
**Problem:** Services return ad-hoc dictionaries with inconsistent structure
**Solution:** Typed result DTOs for complex operations
```python
class ArticleProcessingResult(SQLModel):  # ✅ High value
    article_id: int
    entities_extracted: int
    analysis_completed: bool
    processing_duration_ms: int
    status: Literal["completed", "failed", "partial"]
    error_message: Optional[str] = None
```

#### **4. Error Response DTOs**
**Problem:** Inconsistent error formatting across API and CLI
**Solution:** Standardized error responses
```python
class ErrorResponse(SQLModel):  # ✅ High value
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
```

### ❌ **Low-Value DTOs (Don't Create These)**

#### **1. Basic Create DTOs**
**SQLModel handles this naturally:**
```python
# ❌ Don't create this
class ArticleCreate(SQLModel):
    title: str
    content: str
    url: str

# ✅ Use SQLModel directly
article = Article(title="...", content="...", url="...")
# Auto-generated fields (id, timestamps) excluded automatically
```

#### **2. Basic Update DTOs**
**Dict approach works fine for partial updates:**
```python
# ❌ Don't create this
class ArticleUpdate(SQLModel):
    title: Optional[str] = None
    content: Optional[str] = None

# ✅ Use Dict for updates
def update_article(article_id: int, updates: Dict[str, Any]):
    # SQLModel handles partial updates naturally
```

#### **3. Simple CRUD Response DTOs**
**Read DTOs already cover this:**
```python
# ❌ Don't create redundant wrappers
class ArticleResponse(SQLModel):
    article: ArticleRead
    success: bool

# ✅ Return Read DTO directly
def get_article(article_id: int) -> Optional[ArticleRead]:
    # Simple and clear
```

### 🤔 **Maybe Create (Case-by-Case)**

#### **1. Complex Validation DTOs**
**Only if SQLModel validation is insufficient:**
```python
# 🤔 Only if complex business rules needed
class ApifyActorConfigCreate(SQLModel):
    actor_id: str = Field(regex=r"^[a-zA-Z0-9_-]+$")
    schedule: str = Field(regex=r"^(\*|[0-5]?\d)(\s+(\*|[01]?\d|2[0-3])){4}$")  # Cron validation
    # Only create if validation is truly complex
```

#### **2. Bulk Operation DTOs**
**Only if operations are genuinely bulk-specific:**
```python
# 🤔 Only if bulk operations have special requirements
class BulkArticleProcessRequest(SQLModel):
    article_ids: List[int] = Field(min_items=1, max_items=100)
    operation: Literal["analyze", "reprocess", "archive"]
    options: Dict[str, Any] = Field(default_factory=dict)
```

## Implementation Guidelines

### **Naming Conventions**
- **Read DTOs**: `<Model>Read` (e.g., `ArticleRead`)
- **Result DTOs**: `<Operation>Result` (e.g., `ArticleProcessingResult`)
- **List DTOs**: `<Model>ListResponse` or generic `ListResponse[ModelRead]`
- **Error DTOs**: `ErrorResponse`, `ValidationErrorResponse`

### **Field Selection for Read DTOs**
```python
class ArticleRead(SQLModel):
    # ✅ Include all scalar fields
    id: int
    title: str
    content: str
    
    # ✅ Include related entity IDs (not objects)
    entity_ids: List[int] = Field(default_factory=list)
    
    # ❌ Don't include relationships as full objects
    # entities: List[Entity]  # This causes session binding issues
```

### **Validation Patterns**
```python
class ArticleProcessingResult(SQLModel):
    # ✅ Use Literals for known values
    status: Literal["completed", "failed", "partial"]
    
    # ✅ Use Field constraints for validation
    processing_duration_ms: int = Field(ge=0)
    
    # ✅ Use Optional for nullable fields
    error_message: Optional[str] = None
    
    # ✅ Include model config for serialization
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [{"status": "completed", "processing_duration_ms": 1500}]
        }
    }
```

## Anti-Patterns to Avoid

### **1. DTO Proliferation**
```python
# ❌ Don't create DTOs for every possible combination
class ArticleCreateRequest(SQLModel): ...
class ArticleCreateResponse(SQLModel): ...
class ArticleCreateValidation(SQLModel): ...
# This creates maintenance burden without value
```

### **2. Shallow Wrapper DTOs**
```python
# ❌ Don't wrap simple responses unnecessarily
class ArticleGetResponse(SQLModel):
    article: ArticleRead
    
# ✅ Return the DTO directly
def get_article() -> Optional[ArticleRead]:
```

### **3. Premature Optimization**
```python
# ❌ Don't create DTOs for theoretical future needs
class ArticleCacheableRead(SQLModel):  # "We might need caching later"
    # Create DTOs when you have actual requirements
```

## Testing DTO Patterns

### **Read DTO Tests**
```python
def test_article_read_from_sqlmodel():
    article = Article(title="Test", content="Content", url="http://example.com")
    article_read = ArticleRead.model_validate(article)
    assert article_read.title == "Test"
    assert isinstance(article_read.entity_ids, list)
```

### **Result DTO Tests**
```python
def test_processing_result_validation():
    result = ArticleProcessingResult(
        article_id=1,
        status="completed",
        processing_duration_ms=1500
    )
    assert result.status == "completed"
    assert result.error_message is None
```

## Migration Strategy

When adding DTOs to existing code:

1. **Start with high-value DTOs** (List responses, domain results)
2. **Update services incrementally** - one method at a time
3. **Update tests** to verify new return types
4. **Don't break existing APIs** - add DTOs alongside current patterns initially
5. **Remove old patterns** only after DTOs are proven

## Decision Checklist

Before creating any DTO, verify:

- [ ] SQLModel alone cannot solve this problem
- [ ] There's a concrete issue with current approach
- [ ] The DTO will be actively used (not theoretical)
- [ ] The maintenance burden is justified
- [ ] The DTO follows established naming conventions
- [ ] Tests are included for the new DTO pattern

## Examples of Good DTO Candidates

### **ArticleProcessingResult** ✅
- **Problem**: Services return inconsistent dictionaries for processing results
- **Value**: Type safety, consistent structure, clear success/failure indication
- **Usage**: High frequency in article processing pipeline

### **ListResponse[T]** ✅
- **Problem**: Pagination inconsistency across all list endpoints
- **Value**: Standardized pagination, generic reusability
- **Usage**: Every list operation in API

### **ErrorResponse** ✅
- **Problem**: Inconsistent error formats across API and CLI
- **Value**: Standardized error handling, better debugging
- **Usage**: All error cases

Remember: **Quality over quantity** - A few well-designed DTOs that solve real problems are better than comprehensive coverage that adds complexity.