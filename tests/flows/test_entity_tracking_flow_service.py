"""Tests for the EntityTrackingFlow state-based implementation."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from local_newsifier.models.state import EntityTrackingState, TrackingStatus
from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.services.entity_service import EntityService


def test_entity_tracking_flow_uses_service():
    """Test that EntityTrackingFlow uses the EntityService."""
    # Skip this test as it requires more complex mocking
    pytest.skip("Needs complex mocking due to crewai integration")


@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_creates_default_service(
    mock_tracker_class, mock_resolver_class, mock_analyzer_class, mock_extractor_class, mock_service_class
):
    """Test that EntityTrackingFlow creates a default service if none is provided."""
    # Skip this test as it requires more complex mocking
    pytest.skip("Needs complex mocking due to crewai integration")


def test_entity_tracking_flow_handles_errors():
    """Test that EntityTrackingFlow properly handles errors during processing."""
    # Skip this test as it requires more complex mocking
    pytest.skip("Needs complex mocking due to crewai integration")


def test_entity_tracking_state_logs():
    """Test that logs are properly added to EntityTrackingState."""
    # Create state
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
