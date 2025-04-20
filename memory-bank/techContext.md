# Technical Context: Local Newsifier

## Technologies Used

### Core Technologies

1. **Python**: Primary programming language (3.10+)
2. **crew.ai**: Framework for orchestrating workflows and managing state
3. **SQLModel**: ORM for database operations, combining SQLAlchemy and Pydantic
4. **spaCy**: NLP library for entity recognition and text analysis
5. **Poetry**: Dependency management and packaging

### Database

1. **SQLite**: Lightweight database for development and testing
2. **SQLAlchemy**: SQL toolkit and ORM for database operations
3. **Alembic** (implied): Database migration tool

### Testing

1. **pytest**: Testing framework
2. **pytest-cov**: Test coverage reporting
3. **unittest.mock**: Mocking library for tests

### NLP & Analysis

1. **spaCy**: Core NLP functionality
   - `en_core_web_lg` model: Large English model with word vectors
2. **NLTK** (implied): Natural Language Toolkit for text processing

### Development Tools

1. **pre-commit**: Git hooks for code quality checks
2. **GitHub Actions**: CI/CD pipeline

## Development Setup

### Environment Setup

1. **Poetry Installation**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Dependencies Installation**:
   ```bash
   poetry install
   ```

3. **spaCy Model Download**:
   ```bash
   poetry run python -m spacy download en_core_web_lg
   ```

### Database Configuration

The system supports multiple database instances for development:

1. **Standard Database**: Default SQLite database
2. **Cursor-Specific Databases**: Each cursor instance gets its own isolated database
   - Controlled via `CURSOR_DB_ID` environment variable
   - Initialized with `scripts/init_cursor_db.py`

### Running the Application

1. **News Pipeline**:
   ```bash
   poetry run python scripts/run_pipeline.py --url <URL>
   ```

2. **Headline Trend Analysis**:
   ```bash
   poetry run python scripts/demo_headline_trends.py --days 30 --interval day
   ```

3. **Entity Tracking** (implied):
   ```bash
   poetry run python scripts/demo_entity_tracking.py
   ```

### Testing

1. **Basic Test Execution**:
   ```bash
   poetry run pytest
   ```

2. **With Coverage**:
   ```bash
   poetry run pytest --cov=src/local_newsifier
   ```

3. **With Detailed Output**:
   ```bash
   poetry run pytest -v --durations=0
   ```

## Technical Constraints

### Performance Constraints

1. **NLP Processing Speed**: spaCy model loading and processing is computationally intensive
   - Large models require significant memory
   - Processing time scales with article length

2. **Database Performance**: SQLite has limitations for concurrent access
   - Not suitable for high-concurrency production use
   - Appropriate for development and testing

### Dependency Constraints

1. **spaCy Model Size**: The `en_core_web_lg` model is large (~560MB)
   - Requires sufficient disk space and memory
   - Initial loading time can be significant

2. **Python Version Compatibility**: Tested on Python 3.10, 3.11, and 3.12
   - Some dependencies may have version-specific requirements

### Operational Constraints

1. **Network Dependency**: Web scraping requires network access
   - Subject to rate limiting, blocking, or content changes
   - Network errors must be handled gracefully

2. **Content Parsing Challenges**: HTML structure varies across news sources
   - Parsing logic must be robust to handle variations
   - May require source-specific adaptations

### Scalability Constraints

1. **SQLite Limitations**: Not suitable for high-volume production use
   - Single-writer, multiple-reader concurrency model
   - Limited to local filesystem access

2. **Memory Usage**: NLP processing can be memory-intensive
   - Large articles or batch processing may require significant RAM
   - Model loading adds overhead to startup time

## Tool Usage Patterns

### Database Access

```python
# Session management with context manager
with Session(engine) as session:
    # Database operations
    articles = session.exec(select(Article)).all()

# Session management with decorator
@with_session
def function(session: Session = None):
    # Database operations using provided session
    session.exec(...)
```

### Flow Definition

```python
class CustomFlow(Flow):
    def __init__(self, param1, param2):
        super().__init__()
        self.tool1 = Tool1()
        self.tool2 = Tool2()
    
    def task1(self, state):
        # Process state with tool1
        return self.tool1.process(state)
    
    def task2(self, state):
        # Process state with tool2
        return self.tool2.process(state)
```

### State Management

```python
# Initialize state
state = NewsAnalysisState(target_url=url)

# Update state
state.status = AnalysisStatus.SCRAPE_SUCCEEDED
state.add_log("Scraping completed successfully")

# Error handling
if error:
    state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
    state.error_details = str(error)
```

### NLP Processing

```python
# Load spaCy model
nlp = spacy.load("en_core_web_lg")

# Process text
doc = nlp(text)

# Extract entities
entities = [ent for ent in doc.ents if ent.label_ == "PERSON"]

# Analyze context
context = entity.sent.text
```

## Deployment Considerations

While not explicitly documented, the system appears designed for:

1. **Local Development**: Primary use case with SQLite database
2. **Potential Production Deployment**: Would likely require:
   - Migration to a more robust database (PostgreSQL, MySQL)
   - Containerization (Docker)
   - Scheduled execution for regular updates
   - API layer for accessing analysis results
