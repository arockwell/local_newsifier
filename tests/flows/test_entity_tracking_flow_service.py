"""Tests for the EntityTrackingFlow that uses the updated EntityTracker."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

def test_entity_tracking_flow_uses_new_tracker():
    """Test that EntityTrackingFlow uses the updated EntityTracker."""
    # Arrange
    mock_tracker = MagicMock()
    mock_tracker.process_article.return_value = [
        {
            "original_text": "John Doe",
            "canonical_name": "John Doe",
            "canonical_id": 1,
            "context": "John Doe visited the city.",
            "sentiment_score": 0.5,
            "framing_category": "neutral"
        }
    ]
    
    # Create test state
    from local_newsifier.models.state import EntityTrackingState
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Create flow with mock tracker
    from local_newsifier.flows.entity_tracking_flow_service import EntityTrackingFlow
    flow = EntityTrackingFlow(entity_tracker=mock_tracker)
    
    # Act
    result_state = flow.process(state)
    
    # Assert
    mock_tracker.process_article.assert_called_once_with(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    assert result_state.status == "SUCCESS"
    assert len(result_state.entities) == 1
    assert result_state.entities[0]["original_text"] == "John Doe"
