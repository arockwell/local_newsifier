# System Patterns: Local Newsifier

## System Architecture

Local Newsifier follows a modular, layered architecture that separates concerns and enables independent development and testing of components. The system is built around the following key architectural patterns:

### 1. Flow-Based Processing

The system uses crew.ai Flows to orchestrate multi-step processing pipelines. Each Flow represents a complete workflow (like news processing or entity tracking) and manages the execution of individual tasks within that workflow.

```
┌─────────────────────────┐
│       Flow Layer        │
│  (Orchestration Logic)  │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│      Tool Layer         │
│  (Processing Logic)     │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│      Model Layer        │
│  (Data Representation)  │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│      CRUD Layer         │
│  (Data Access Logic)    │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│    Database Layer       │
│  (Data Persistence)     │
└─────────────────────────┘
```

### 2. State-Based Processing

Each Flow operates on a State object that encapsulates the current status of processing, input data, intermediate results, and error information. This enables:

- Resumable processing after failures
- Clear tracking of progress
- Comprehensive error handling
- Audit trails of processing steps

### 3. Repository Pattern

The CRUD layer implements the Repository pattern to abstract database operations and provide a clean interface for data access. Each entity type has its own repository that handles:

- Creating new records
- Retrieving existing records
- Updating record data
- Deleting records
- Specialized queries

## Key Design Patterns

### 1. Dependency Injection

Components receive their dependencies through constructor parameters, enabling:
- Easier testing through mock injection
- Flexible configuration
- Reduced coupling between components

Example:
```python
class EntityTracker:
    def __init__(self, session: Optional[Session] = None, model_name: str = "en_core_web_lg"):
        self.session = session
        self.nlp = spacy.load(model_name)
```

### 2. Decorator Pattern

The system uses decorators to add cross-cutting concerns like session management:

```python
@with_session
def process_article(self, article_id: int, *, session: Session = None) -> List[Dict]:
    # Session handling is abstracted away by the decorator
    # ...
```

### 3. Factory Pattern

Factory methods are used to create complex objects, particularly for database connections:

```python
def get_session():
    # Logic to create and configure a database session
    # ...
    yield session
```

### 4. Strategy Pattern

Different analysis strategies can be plugged into the system, allowing for flexible processing approaches:

```python
# Different analyzer implementations can be used interchangeably
self.analyzer = NERAnalyzerTool()  # Could be swapped with another analyzer
```

### 5. Observer Pattern

The system implements a form of the Observer pattern through its logging and state tracking, where processing steps update state and logs that can be observed externally.

## Component Relationships

### 1. Flow Components

Flows orchestrate the overall processing and contain the high-level business logic:

- `NewsPipelineFlow`: Manages the end-to-end process of fetching, analyzing, and storing news articles
- `EntityTrackingFlow`: Handles the identification and tracking of entities across articles
- `HeadlineTrendFlow`: Analyzes trends in headlines over time

### 2. Tool Components

Tools implement specific processing logic and are used by Flows:

- `WebScraperTool`: Fetches article content from URLs
- `NERAnalyzerTool`: Performs Named Entity Recognition on article content
- `EntityTracker`: Tracks entities across multiple articles
- `HeadlineTrendAnalyzer`: Analyzes trends in headlines

### 3. Model Components

Models represent the data structures used throughout the system:

- Database Models: SQLModel-based ORM models for database entities
- State Models: Pydantic models for representing processing state
- Pydantic Models: Data validation and serialization models

### 4. CRUD Components

CRUD modules handle database operations for specific entity types:

- `article.py`: Operations for Article entities
- `entity.py`: Operations for Entity entities
- `analysis_result.py`: Operations for AnalysisResult entities

## Critical Implementation Paths

### 1. News Article Processing Path

```
URL Input → WebScraperTool → NERAnalyzerTool → FileWriterTool → Database
```

This path handles the core functionality of fetching and analyzing news articles.

### 2. Entity Tracking Path

```
Article Data → EntityTracker → EntityResolver → ContextAnalyzer → Database
```

This path manages the identification and tracking of entities across articles.

### 3. Headline Trend Analysis Path

```
Date Range → HeadlineTrendAnalyzer → Keyword Extraction → Trend Detection → Report Generation
```

This path analyzes trends in headlines over specified time periods.

## Error Handling Patterns

1. **State-Based Error Tracking**: Errors are captured in the state object with detailed information
2. **Typed Error States**: Different error types (network, parsing, etc.) have specific state values
3. **Retry Logic**: Flows implement retry logic for recoverable errors
4. **Graceful Degradation**: System can continue partial processing when some components fail

## Data Flow Patterns

1. **Extract-Transform-Load (ETL)**: The system follows an ETL pattern for processing news articles
2. **Incremental Processing**: New articles are processed incrementally as they are discovered
3. **Batch Analysis**: Trend analysis is performed in batches over specified time periods
4. **Event Sourcing**: Entity tracking maintains a history of entity mentions over time
