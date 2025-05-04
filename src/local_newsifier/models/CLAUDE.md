# Local Newsifier Models Guide

## Overview
The models module contains all data models used in the Local Newsifier system. These include SQLModel-based database models as well as Pydantic models for state management and data transfer.

## Key Model Types

### Database Models (SQLModel)
- **Article**: News articles with title, content, URL, etc.
- **Entity**: Entities extracted from articles (people, places, organizations)
- **CanonicalEntity**: Normalized entity references
- **EntityRelationship**: Relationships between entities
- **EntityMentionContext**: Context around entity mentions
- **AnalysisResult**: Results from analysis operations
- **RSSFeed**: RSS feed sources configuration
- **FeedProcessingLog**: Logs of RSS feed processing operations
- **ApifySourceConfig**: Configuration for Apify web scraping
- **ApifyJob**: Details of Apify scraping job runs
- **ApifyDatasetItem**: Raw data from Apify scraping jobs

### State Models (Pydantic)
- **EntityTrackingState**: Tracks state during entity extraction and processing
- **TrendAnalysisState**: Tracks state during trend analysis
- **ErrorDetails**: Structured error information

## Common Patterns

### SQLModel Table Definitions
Models use SQLModel with the `table=True` parameter for database tables:

```python
class Article(SQLModel, table=True):
    __tablename__ = "articles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    url: str = Field(unique=True)
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    entities: List["Entity"] = Relationship(back_populates="article")
```

### Relationship Definitions
SQLModel relationships are defined using the `Relationship` type:

```python
# In Entity model
article_id: int = Field(foreign_key="articles.id")
article: "Article" = Relationship(back_populates="entities")

# In Article model
entities: List["Entity"] = Relationship(back_populates="article")
```

### Handling Circular References
For circular type references, use `TYPE_CHECKING` imports:

```python
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .entity import Entity

class Article(SQLModel, table=True):
    # ... fields ...
    
    # Type checker sees this
    entities: List["Entity"] = Relationship(back_populates="article")
```

### Default Timestamps
Models use UTC timestamps for created_at and updated_at fields:

```python
created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

### Field Validation
Use Field validators for data validation:

```python
url: str = Field(unique=True)
confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
```

### JSON Fields
For JSON/dictionary data in PostgreSQL:

```python
input_configuration: Dict[str, Any] = Field(default_factory=dict, sa_type=JSON)
```

### Enum Fields
For fields with a fixed set of values, use Python Enums:

```python
class EntityType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    EVENT = "EVENT"
    OTHER = "OTHER"

class Entity(SQLModel, table=True):
    # ...
    entity_type: EntityType
```

## State Models
State models use Pydantic to track process state:

```python
class EntityTrackingState(BaseModel):
    run_id: UUID = Field(default_factory=uuid4)
    article_id: int
    content: str
    title: str
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    status: TrackingStatus = Field(default=TrackingStatus.INITIALIZED)
    error_details: Optional[ErrorDetails] = None
    
    def add_log(self, message: str):
        """Add a log message to the state."""
        self.run_logs.append(f"[{datetime.now(timezone.utc)}] {message}")
        self.last_updated = datetime.now(timezone.utc)
```

## Best Practices

### SQLModel vs Pydantic Models
- Use SQLModel for database tables (`table=True`)
- Use Pydantic models (BaseModel) for request/response data and state
- Use SQLModel without `table=True` for models that combine database data

### Handling Database Objects
- Never pass SQLModel objects between sessions
- Use IDs for cross-session references
- If needed, refresh objects in new sessions

### Model Serialization
- Use `model_dump()` not `dict()` for SQLModel objects
- For JSON serialization, handle datetime objects:

```python
def serialize_model(model):
    """Serialize a model to a JSON-compatible dict."""
    data = model.model_dump()
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data
```

### Multiple Table Inheritance
When inheritance is needed, use SQLModel's table inheritance:

```python
class BaseEntity(SQLModel, table=True):
    __tablename__ = "base_entities"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    
class SpecializedEntity(BaseEntity, table=True):
    __tablename__ = "specialized_entities"
    
    id: Optional[int] = Field(default=None, primary_key=True, foreign_key="base_entities.id")
    special_field: str
```

### Table Names
- Use plural form for table names (`articles`, not `article`)
- Use snake_case for multi-word tables (`feed_processing_logs`)
- Be consistent with naming conventions

### Schema Migrations
- Never modify model fields without creating a migration
- Use Alembic for database migrations
- Test migrations in development before applying to production