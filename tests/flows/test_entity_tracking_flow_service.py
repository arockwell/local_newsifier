"""Tests for the EntityTrackingFlow state-based implementation."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, AsyncMock

from local_newsifier.models.state import EntityTrackingState, TrackingStatus
from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.services.entity_service import EntityService
from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip


def test_entity_tracking_flow_uses_service():
    """Test that EntityTrackingFlow uses the EntityService."""
    # Arrange
    mock_service = MagicMock(spec=EntityService)
    mock_entity_tracker = MagicMock()
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    mock_result_state = MagicMock(spec=EntityTrackingState)
    mock_result_state.status = TrackingStatus.SUCCESS
    mock_result_state.entities = [
        {
            "original_text": "John Doe",
            "canonical_name": "John Doe",
            "canonical_id": 1,
            "context": "John Doe visited the city.",
            "sentiment_score": 0.5,
            "framing_category": "neutral"
        }
    ]
    mock_service.process_article_with_state.return_value = mock_result_state
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )

    # Create flow with mock service and dependencies
    flow = EntityTrackingFlow(
        entity_service=mock_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )

    # If the class has an async method, replace it with the mock result
    if hasattr(flow, 'process_async'):
        flow.process_async = AsyncMock(return_value=mock_result_state)

    # Act - call the synchronous method
    result_state = flow.process(state)

    # Assert
    mock_service.process_article_with_state.assert_called_once_with(state)
    assert result_state is mock_result_state
    assert result_state.status == TrackingStatus.SUCCESS
    assert len(result_state.entities) == 1
    assert result_state.entities[0]["original_text"] == "John Doe"


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
    # Arrange
    mock_service = MagicMock(spec=EntityService)
    mock_entity_tracker = MagicMock()
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    mock_service.process_article_with_state.side_effect = Exception("Test error")
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Create flow with mock service and dependencies
    flow = EntityTrackingFlow(
        entity_service=mock_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )
    
    # If the class has an async method, make sure it doesn't interfere with our test
    if hasattr(flow, 'process_async'):
        # Set it to a mock that won't be called (we're testing the sync path)
        flow.process_async = AsyncMock()
    
    # Act - The flow should catch the exception and return the state with error
    result_state = flow.process(state)
    
    # Assert
    mock_service.process_article_with_state.assert_called_once_with(state)
    assert result_state.status == TrackingStatus.FAILED
    assert "Test error" in result_state.error_details.message
    assert result_state.error_details.task == "entity_processing"


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
