"""Tests for the EntityTrackingFlow that uses the updated EntityTracker."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from local_newsifier.models.state import EntityTrackingState, TrackingStatus
from local_newsifier.flows.entity_tracking_flow_service import EntityTrackingFlow


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
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )

    # Create flow with mock tracker
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

    assert result_state.status == TrackingStatus.SUCCESS
    assert len(result_state.entities) == 1
    assert result_state.entities[0]["original_text"] == "John Doe"


def test_entity_tracking_flow_creates_default_tracker():
    """Test that EntityTrackingFlow creates a default tracker if none is provided."""
    # Create flow without providing a tracker
    with patch("local_newsifier.flows.entity_tracking_flow_service.EntityTracker") as mock_tracker_class:
        mock_tracker = MagicMock()
        mock_tracker_class.return_value = mock_tracker
        
        flow = EntityTrackingFlow()
        
        # Verify the tracker was created
        mock_tracker_class.assert_called_once()
        assert flow.entity_tracker == mock_tracker


def test_entity_tracking_flow_handles_errors():
    """Test that EntityTrackingFlow properly handles errors during processing."""
    # Arrange
    mock_tracker = MagicMock()
    mock_tracker.process_article.side_effect = Exception("Test error")
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Create flow with mock tracker
    flow = EntityTrackingFlow(entity_tracker=mock_tracker)
    
    # Act
    result_state = flow.process(state)
    
    # Assert
    mock_tracker.process_article.assert_called_once()
    assert result_state.status == TrackingStatus.FAILED
    assert "Test error" in result_state.error_details.message
    assert result_state.error_details.task == "entity_tracking"
    assert len(result_state.run_logs) > 1  # Should have at least the starting log and the error log


def test_entity_tracking_state_logs():
    """Test that logs are properly added to EntityTrackingState."""
    # Create state and flow
    state = EntityTrackingState(
        article_id=1,
        content="Test content",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Add some logs
    state.add_log("Test log 1")
    state.add_log("Test log 2")
    
    # Verify logs
    assert len(state.run_logs) == 2
    assert "Test log 1" in state.run_logs[0]
    assert "Test log 2" in state.run_logs[1]
    assert "[" in state.run_logs[0]  # Should have timestamp
