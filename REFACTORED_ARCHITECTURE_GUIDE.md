# Refactored Architecture Implementation Guide

This document provides guidance on how to implement the new architecture throughout the codebase.

## Completed Components

The following components have already been implemented with the new architecture:

- **SessionManager** (`src/local_newsifier/database/session_manager.py`)
- **EntityService** (`src/local_newsifier/services/entity_service.py`) - Contains all entity-related business logic
- **SentimentService** (`src/local_newsifier/services/sentiment_service.py`) - Contains sentiment analysis business logic
- **EntityTrackingFlow V2** (`src/local_newsifier/flows/entity_tracking_flow_v2.py`) - Uses EntityService directly
- **Factory Classes** (`src/local_newsifier/core/factory.py`)

## Implementation Steps

Follow these steps to implement the new architecture for other components:

### 1. Create Service Layer with All Business Logic

For each domain area in the application, create a comprehensive service class that contains all the business logic:

```python
# src/local_newsifier/services/sentiment_service.py
from datetime import datetime
from typing import Dict, List, Optional

from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud

class SentimentService:
    """Service for sentiment analysis business logic."""

    def __init__(self, session_manager=None):
        """Initialize the sentiment service."""
        self.session_manager = session_manager or get_session_manager()
        
    def store_sentiment_analysis(self, article_id, sentiment_score, sentiment_details):
        """Store sentiment analysis results."""
        with self.session_manager.session() as session:
            # Implementation...
            pass
            
    def get_sentiment_trends(self, start_date, end_date):
        """Get sentiment trends over time."""
        with self.session_manager.session() as session:
            # Implementation...
            pass
            
    def process_article(self, article_id, content, title):
        """Process an article's sentiment from start to finish."""
        # Complete processing logic within the service
        # This eliminates the need for a separate tool layer
```

### 2. Create Tools Only When Needed

Only create separate tool classes when they provide functionality beyond what belongs in a service:

```python
# src/local_newsifier/tools/sentiment_analyzer_v2.py
import spacy
from typing import Dict, List

from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.services.sentiment_service import SentimentService

class SentimentAnalyzer:
    """Tool for analyzing sentiment in articles."""

    def __init__(
        self,
        sentiment_service=None,
        session_manager=None,
        model_name="en_core_web_lg"
    ):
        """Initialize the sentiment analyzer."""
        self.session_manager = session_manager or get_session_manager()
        self.sentiment_service = sentiment_service or SentimentService(
            session_manager=self.session_manager
        )
        # Load spaCy model...
        
    def analyze_article(self, article_id, content, title):
        """Analyze an article's sentiment."""
        # Implementation that uses NLP/ML capabilities
        # Delegates business logic to the service
```

### 3. Update Factory Classes with Focus on Services

Add factory methods primarily for services, with tools only when necessary:

```python
# src/local_newsifier/core/factory.py
# Add to existing class:

class ServiceFactory:
    # ... existing code ...
    
    @staticmethod
    def create_sentiment_service(session_manager=None, model_name="en_core_web_lg"):
        """Create a SentimentService instance."""
        return SentimentService(
            session_manager=session_manager or get_session_manager(),
            model_name=model_name
        )

class ToolFactory:
    # Only needed for specialized tools that aren't just business logic
    
    @staticmethod
    def create_sentiment_analyzer(
        session_manager=None,
        sentiment_service=None,
        model_name="en_core_web_lg"
    ):
        """Create a SentimentAnalyzer instance."""
        sm = session_manager or get_session_manager()
        svc = sentiment_service or ServiceFactory.create_sentiment_service(
            session_manager=sm
        )
        return SentimentAnalyzer(
            sentiment_service=svc,
            session_manager=sm,
            model_name=model_name
        )
```

### 4. Refactor Flows to Use Services Directly

Update flows to use services directly, bypassing tools when possible:

```python
# src/local_newsifier/flows/sentiment_analysis_flow_v2.py
from datetime import datetime, timedelta
from typing import Dict, List

from crewai import Flow

from local_newsifier.core.factory import ServiceFactory
from local_newsifier.database.session_manager import get_session_manager

class SentimentAnalysisFlow(Flow):
    """Flow for analyzing sentiment in articles."""

    def __init__(
        self,
        session_manager=None,
        sentiment_service=None
    ):
        """Initialize the sentiment analysis flow."""
        super().__init__()
        self.session_manager = session_manager or get_session_manager()
        self.sentiment_service = sentiment_service or ServiceFactory.create_sentiment_service(
            session_manager=self.session_manager
        )
        
    def analyze_new_articles(self):
        """Analyze new articles for sentiment."""
        with self.session_manager.session() as session:
            # Implementation using sentiment_service directly...
            pass
```

### 5. Update Tests

Create or update tests for the new components:

```python
# tests/services/test_sentiment_service.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from local_newsifier.services.sentiment_service import SentimentService

class TestSentimentService:
    """Test cases for SentimentService."""
    
    @patch('local_newsifier.services.sentiment_service.analysis_result_crud')
    def test_store_sentiment_analysis(self, mock_crud):
        """Test storing sentiment analysis."""
        # Setup
        service = SentimentService()
        mock_session = MagicMock()
        
        # Create mock session manager
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        service.session_manager = mock_session_manager
        
        # Call method
        service.store_sentiment_analysis(1, 0.5, {"positive": 0.7, "negative": 0.3})
        
        # Assert
        mock_crud.create.assert_called_once()
```

## Migration Strategy

Follow this strategy to migrate the codebase:

1. **Start with Services**: Implement service classes that encapsulate all domain logic.
2. **Consolidate Logic**: Move business logic from tools directly into services when possible.
3. **Update Flows**: Refactor flows to use services directly.
4. **Update Factory Classes**: Add factory methods primarily for services.
5. **Write Tests**: Create or update tests focusing mainly on services.
6. **Gradual Rollout**: Use version suffixes (e.g., `_v2`) to allow gradual migration without breaking existing code.

## Migration Examples

See these files for migration examples:

- `scripts/migrate_to_new_architecture.py`: Demonstrates migration patterns
- `scripts/demo_refactored_architecture.py`: Shows how to use the new architecture

## Testing the Migration

To test the migration, run:

```bash
# Run all tests for the new architecture
./run_refactored_tests.sh

# Run specific service tests
pytest tests/services/test_entity_service.py

# Run the demo script
python scripts/demo_refactored_architecture.py
```

## Best Practices

- **Services as Central Components**: Put all business logic in services.
- **Limit Tool Layer**: Only use tools for specialized functionality that doesn't belong in services.
- **Direct Flow-to-Service Communication**: Have flows use services directly when possible.
- **Dependency Injection**: Always accept dependencies in constructors.
- **Default Dependencies**: Provide sensible defaults for dependencies.
- **Consistent Session Management**: Use the SessionManager for all database operations.
- **Factory Usage**: Use factories to create complex objects with dependencies.
- **Testing**: Focus tests on services since they contain the core business logic.
- **Documentation**: Document all public APIs and update as components change.
