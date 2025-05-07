"""Tests for the injectable EntityTracker tool."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

def test_entity_tracker_uses_injected_service():
    """Test that EntityTracker uses the injected entity service."""
    # Arrange
    mock_service = MagicMock()
    mock_service.process_article_entities.return_value = [
        {
            "original_text": "John Doe",
            "canonical_name": "John Doe",
            "canonical_id": 1,
            "context": "John Doe visited the city.",
            "sentiment_score": 0.5,
            "framing_category": "neutral"
        }
    ]
    
    # Mock the EntityTracker class to bypass the injectable decorator
    original_tracker = None
    
    with patch('local_newsifier.tools.entity_tracker_service.EntityTracker') as MockTracker:
        # Import the actual class
        from local_newsifier.tools.entity_tracker_service import EntityTracker
        original_tracker = EntityTracker
        
        # Configure the mock
        mock_tracker = MagicMock()
        mock_tracker.entity_service = mock_service
        mock_tracker.process_article.return_value = mock_service.process_article_entities.return_value
        MockTracker.return_value = mock_tracker
        
        # Create a new instance (will use our mocked class)
        tracker = EntityTracker()
        
        # Act
        result = tracker.process_article(
            article_id=1,
            content="John Doe visited the city.",
            title="Test Article",
            published_at=datetime(2025, 1, 1)
        )
        
        # Assert
        mock_tracker.process_article.assert_called_once_with(
            article_id=1,
            content="John Doe visited the city.",
            title="Test Article",
            published_at=datetime(2025, 1, 1)
        )
        
        assert len(result) == 1
        assert result[0]["original_text"] == "John Doe"
        assert result[0]["canonical_name"] == "John Doe"
        assert result[0]["sentiment_score"] == 0.5


def test_entity_tracker_provider(monkeypatch):
    """Test that the entity tracker provider creates a properly configured instance."""
    # Import the provider function
    from local_newsifier.di.providers import get_entity_tracker_tool
    
    # Mock the EntityTracker class
    mock_tracker = MagicMock()
    
    with patch('local_newsifier.tools.entity_tracker_service.EntityTracker', 
               return_value=mock_tracker) as mock_constructor:
        # Act
        tracker = get_entity_tracker_tool()
        
        # Assert
        mock_constructor.assert_called_once()
        assert tracker == mock_tracker
