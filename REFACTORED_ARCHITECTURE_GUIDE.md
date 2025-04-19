# Refactored Architecture Implementation Guide

This document provides guidance on how to implement the new architecture throughout the codebase.

## Completed Components

The following components have already been implemented with the new architecture:

- **SessionManager** (`src/local_newsifier/database/session_manager.py`)
- **EntityService** (`src/local_newsifier/services/entity_service.py`)
- **EntityTracker V2** (`src/local_newsifier/tools/entity_tracker_v2.py`)
- **EntityTrackingFlow V2** (`src/local_newsifier/flows/entity_tracking_flow_v2.py`) 
- **Factory Classes** (`src/local_newsifier/core/factory.py`)

## Implementation Steps

Follow these steps to implement the new architecture for other components:

### 1. Create Service Layer

For each domain area in the application, create a service class:

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
```

### 2. Refactor Tools to Use Services

Refactor tools to use services and accept dependencies:

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
        # Implementation...
        # Use self.sentiment_service to store results
```

### 3. Update Factory Classes

Add factory methods for new components:

```python
# src/local_newsifier/core/factory.py
# Add to existing class:

class ServiceFactory:
    # ... existing code ...
    
    @staticmethod
    def create_sentiment_service(session_manager=None):
        """Create a SentimentService instance."""
        return SentimentService(
            session_manager=session_manager or get_session_manager()
        )

class ToolFactory:
    # ... existing code ...
    
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

### 4. Refactor Flows

Update flows to use the new tools and services:

```python
# src/local_newsifier/flows/sentiment_analysis_flow_v2.py
from datetime import datetime, timedelta
from typing import Dict, List

from crewai import Flow

from local_newsifier.core.factory import ToolFactory, ServiceFactory
from local_newsifier.database.session_manager import get_session_manager

class SentimentAnalysisFlow(Flow):
    """Flow for analyzing sentiment in articles."""

    def __init__(
        self,
        session_manager=None,
        sentiment_analyzer=None
    ):
        """Initialize the sentiment analysis flow."""
        super().__init__()
        self.session_manager = session_manager or get_session_manager()
        self.sentiment_analyzer = sentiment_analyzer or ToolFactory.create_sentiment_analyzer(
            session_manager=self.session_manager
        )
        
    def analyze_new_articles(self):
        """Analyze new articles for sentiment."""
        with self.session_manager.session() as session:
            # Implementation...
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

1. **Start with Services**: Implement service classes first, as they encapsulate the core business logic.
2. **Update Tools**: Refactor tools to use services and accept dependencies.
3. **Update Flows**: Refactor flows to use the new tools and services.
4. **Update Factory Classes**: Add factory methods for the new components.
5. **Write Tests**: Create or update tests to verify the new components work correctly.
6. **Gradual Rollout**: Use version suffixes (e.g., `_v2`) to allow gradual migration without breaking existing code.

## Migration Examples

See these files for migration examples:

- `scripts/migrate_to_new_architecture.py`: Demonstrates migration patterns
- `scripts/demo_refactored_architecture.py`: Shows how to use the new architecture

## Testing the Migration

To test the migration, run:

```bash
# Run tests for the new architecture
pytest tests/test_refactored_architecture.py

# Run specific service tests
pytest tests/services/test_entity_service.py

# Run the demo script
python scripts/demo_refactored_architecture.py
```

## Best Practices

- **Dependency Injection**: Always accept dependencies in constructors.
- **Default Dependencies**: Provide sensible defaults for dependencies.
- **Consistent Session Management**: Use the SessionManager for all database operations.
- **Factory Usage**: Use factories to create complex objects with dependencies.
- **Testing**: Write tests for services that mock the database operations.
- **Documentation**: Document all public APIs and update as components change.
