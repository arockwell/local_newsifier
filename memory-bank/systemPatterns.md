# System Patterns: Local Newsifier

## System Architecture

Local Newsifier is evolving toward a hybrid architecture that combines the strengths of its current layered approach with improved tool APIs, a dedicated repository layer, and a service layer for business logic. The system architecture includes:

### 1. Hybrid Layered Architecture

The system is transitioning to a hybrid layered architecture that separates concerns more effectively:

```
┌─────────────────────────┐
│       Flow Layer        │
│  (Orchestration Logic)  │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│      Service Layer      │
│  (Business Logic)       │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│      Tool Layer         │
│  (Processing Logic)     │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│      Repository Layer   │
│  (Data Access Logic)    │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│      Model Layer        │
│  (Data Representation)  │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│    Database Layer       │
│  (Data Persistence)     │
└─────────────────────────┘
```

### 2. Flow-Based Processing

The system uses crew.ai Flows to orchestrate multi-step processing pipelines. Each Flow represents a complete workflow (like news processing or entity tracking) and manages the execution of individual tasks within that workflow. In the hybrid architecture, flows are simplified to focus on orchestration, delegating business logic to services.

### 3. Service Layer

The service layer is being implemented to:
- Encapsulate business logic
- Coordinate between multiple tools
- Manage transactions
- Provide a clean API for flows

We have successfully implemented the EntityService, which:
- Coordinates entity extraction, resolution, and context analysis
- Manages database operations through CRUD modules
- Handles transaction boundaries
- Provides a clean API for the EntityTrackingFlow

Services act as the primary interface for flows, abstracting away the details of tool coordination and data access.

### 4. Single-Responsibility Tools

Tools are being refactored to follow the Single Responsibility Principle:
- Each tool performs one specific function
- Tools focus on processing logic, not data access
- Tools have clear input/output contracts
- Tools can be composed and reused flexibly

### 5. Repository Pattern

The repository layer abstracts database operations and provides a clean interface for data access. Each entity type has its own repository that handles:

- Creating new records
- Retrieving existing records
- Updating record data
- Deleting records
- Specialized queries
- Transaction management

### 6. State-Based Processing

Each Flow operates on a State object that encapsulates the current status of processing, input data, intermediate results, and error information. This enables:

- Resumable processing after failures
- Clear tracking of progress
- Comprehensive error handling
- Audit trails of processing steps

## Key Design Patterns

### 1. Interface-Based Design

The hybrid architecture emphasizes interface-based design:
- Components define interfaces separate from implementations
- Dependencies are declared as interfaces, not concrete classes
- This enables loose coupling and easier testing

Example:
```python
class EntityResolver(ABC):
    @abstractmethod
    def resolve_entity(self, entity_text, entity_type):
        pass

class SpacyEntityResolver(EntityResolver):
    def resolve_entity(self, entity_text, entity_type):
        # Implementation using spaCy
        pass
```

### 2. Dependency Injection

Components receive their dependencies through constructor parameters, enabling:
- Easier testing through mock injection
- Flexible configuration
- Reduced coupling between components

Example:
```python
class EntityService:
    def __init__(
        self, 
        entity_repository: EntityRepository,
        entity_extractor: EntityExtractor,
        entity_resolver: EntityResolver
    ):
        self.entity_repository = entity_repository
        self.entity_extractor = entity_extractor
        self.entity_resolver = entity_resolver
```

### 3. Repository Pattern

The repository pattern provides a clean abstraction for data access:
- Each entity type has its own repository
- Repositories handle all database operations
- Repositories manage transactions
- Repositories provide specialized query methods

Example:
```python
class EntityRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    def get_by_article(self, article_id):
        with self.session_factory() as session:
            statement = select(Entity).where(Entity.article_id == article_id)
            return session.exec(statement).all()
```

### 4. Service Layer Pattern

The service layer pattern coordinates business operations:
- Services encapsulate business logic
- Services coordinate between multiple tools and repositories
- Services manage transaction boundaries
- Services provide a clean API for flows

Our implemented EntityService follows this pattern:
```python
class EntityService:
    def __init__(
        self,
        entity_crud,
        canonical_entity_crud,
        entity_mention_context_crud,
        entity_profile_crud,
        entity_extractor,
        context_analyzer,
        entity_resolver,
        session_factory
    ):
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.entity_mention_context_crud = entity_mention_context_crud
        self.entity_profile_crud = entity_profile_crud
        self.entity_extractor = entity_extractor
        self.context_analyzer = context_analyzer
        self.entity_resolver = entity_resolver
        self.session_factory = session_factory
    
    def process_article_entities(
        self, 
        article_id: int,
        content: str,
        title: str,
        published_at: datetime
    ) -> List[Dict[str, Any]]:
        """Process entities in an article.
        
        This method:
        1. Extracts entities from the article content
        2. Resolves entities to canonical forms
        3. Analyzes the context of entity mentions
        4. Stores entities and their context in the database
        5. Returns processed entity data
        """
        with self.session_factory() as session:
            # Extract entities
            extracted_entities = self.entity_extractor.extract_entities(content)
            
            # Process each entity
            processed_entities = []
            for entity in extracted_entities:
                # Resolve entity to canonical form
                canonical_entity = self.entity_resolver.resolve_entity(
                    entity.text, entity.entity_type, session=session
                )
                
                # Analyze context
                context_data = self.context_analyzer.analyze_context(
                    entity.text, entity.sentence_context
                )
                
                # Store entity mention
                entity_obj = self.entity_crud.create(
                    session,
                    article_id=article_id,
                    text=entity.text,
                    entity_type=entity.entity_type,
                    sentence_context=entity.sentence_context,
                    canonical_entity_id=canonical_entity.id
                )
                
                # Store context data
                self.entity_mention_context_crud.create(
                    session,
                    entity_id=entity_obj.id,
                    article_id=article_id,
                    context_text=entity.sentence_context,
                    sentiment_score=context_data.sentiment_score,
                    framing_category=context_data.framing_category
                )
                
                # Add to processed entities
                processed_entities.append({
                    "original_text": entity.text,
                    "canonical_name": canonical_entity.name,
                    "canonical_id": canonical_entity.id,
                    "context": entity.sentence_context,
                    "sentiment_score": context_data.sentiment_score,
                    "framing_category": context_data.framing_category
                })
            
            # Commit the transaction
            session.commit()
            
            return processed_entities
```

### 5. Decorator Pattern

The system uses decorators to add cross-cutting concerns like session management:

```python
@with_session
def process_article(self, article_id: int, *, session: Session = None) -> List[Dict]:
    # Session handling is abstracted away by the decorator
    # ...
```

### 6. Factory Pattern

Factory methods are used to create complex objects, particularly for database connections and service instances:

```python
def get_session():
    # Logic to create and configure a database session
    # ...
    yield session

def get_entity_service():
    # Logic to create and configure an entity service
    # ...
    return EntityService(...)
```

### 7. Strategy Pattern

Different analysis strategies can be plugged into the system, allowing for flexible processing approaches:

```python
# Different analyzer implementations can be used interchangeably
self.analyzer = NERAnalyzerTool()  # Could be swapped with another analyzer
```

### 8. Observer Pattern

The system implements a form of the Observer pattern through its logging and state tracking, where processing steps update state and logs that can be observed externally.

## Component Relationships

### 1. Flow Components

Flows orchestrate the overall processing and contain high-level orchestration logic:

- `NewsPipelineFlow`: Manages the end-to-end process of fetching, analyzing, and storing news articles
- `EntityTrackingFlow`: Handles the identification and tracking of entities across articles
- `HeadlineTrendFlow`: Analyzes trends in headlines over time

### 2. Service Components

Services encapsulate business logic and coordinate between tools and repositories:

- `ArticleService`: Manages article fetching, processing, and storage
- `EntityService`: Manages entity extraction, resolution, and tracking
- `AnalysisService`: Manages trend analysis and reporting

### 3. Tool Components

Tools implement specific processing logic:

- `EntityExtractor`: Extracts entities from text content
- `EntityResolver`: Resolves entities to canonical forms
- `ContextAnalyzer`: Analyzes the context of entity mentions
- `HeadlineKeywordExtractor`: Extracts keywords from headlines
- `TrendDetector`: Detects trends in time-series data

### 4. Repository Components

Repositories handle database operations for specific entity types:

- `ArticleRepository`: Operations for Article entities
- `EntityRepository`: Operations for Entity entities
- `CanonicalEntityRepository`: Operations for CanonicalEntity entities
- `AnalysisResultRepository`: Operations for AnalysisResult entities

### 5. Model Components

Models represent the data structures used throughout the system:

- Database Models: SQLModel-based ORM models for database entities
- State Models: Pydantic models for representing processing state
- Pydantic Models: Data validation and serialization models

## Critical Implementation Paths

### 1. News Article Processing Path

```
URL Input → Flow → ArticleService → WebScraperTool → EntityExtractor → ArticleRepository → Database
```

This path handles the core functionality of fetching and analyzing news articles.

### 2. Entity Tracking Path

```
Article Data → EntityTrackingFlow → EntityTracker → EntityService → EntityExtractor → EntityResolver → ContextAnalyzer → CRUD Operations → Database
```

This path manages the identification and tracking of entities across articles. We have implemented this complete path with our vertical slice approach.

### 3. Headline Trend Analysis Path

```
Date Range → Flow → AnalysisService → HeadlineKeywordExtractor → TrendDetector → Report Generation
```

This path analyzes trends in headlines over specified time periods.

## Error Handling Patterns

1. **Consistent Exception Hierarchy**: A structured hierarchy of exceptions for different error types
2. **Transaction Management**: Proper transaction boundaries with rollback on errors
3. **State-Based Error Tracking**: Errors are captured in the state object with detailed information
4. **Typed Error States**: Different error types (network, parsing, etc.) have specific state values
5. **Retry Logic**: Flows implement retry logic for recoverable errors
6. **Graceful Degradation**: System can continue partial processing when some components fail

## Data Flow Patterns

1. **Extract-Transform-Load (ETL)**: The system follows an ETL pattern for processing news articles
2. **Incremental Processing**: New articles are processed incrementally as they are discovered
3. **Batch Analysis**: Trend analysis is performed in batches over specified time periods
4. **Event Sourcing**: Entity tracking maintains a history of entity mentions over time
