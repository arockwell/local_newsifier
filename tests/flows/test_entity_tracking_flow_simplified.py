"""Tests for the simplified EntityTrackingFlow implementation."""

from datetime import datetime
from unittest.mock import Mock, MagicMock

import pytest
from sqlmodel import Session

from local_newsifier.flows.entity_tracking_flow_simplified import EntityTrackingFlow
from local_newsifier.models.state import EntityTrackingState, TrackingStatus
from local_newsifier.services.entity_service import EntityService
from local_newsifier.tools.entity_tracker_service import EntityTracker
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer
from local_newsifier.tools.resolution.entity_resolver import EntityResolver


def test_entity_tracking_flow_with_explicit_dependencies():
    """Test with explicitly provided dependencies."""
    # Arrange - Create mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock(spec=EntityTracker)
    mock_entity_extractor = Mock(spec=EntityExtractor)
    mock_context_analyzer = Mock(spec=ContextAnalyzer)
    mock_entity_resolver = Mock(spec=EntityResolver)
    
    # Setup mock responses
    mock_result_state = Mock(spec=EntityTrackingState)
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
    mock_entity_service.process_article_with_state.return_value = mock_result_state
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )

    # Act - Initialize flow with explicit dependencies
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )
    
    # Call process method
    result_state = flow.process(state)

    # Assert - Verify correct dependencies were used
    mock_entity_service.process_article_with_state.assert_called_once_with(state)
    assert result_state is mock_result_state
    assert result_state.status == TrackingStatus.SUCCESS
    assert len(result_state.entities) == 1
    assert result_state.entities[0]["original_text"] == "John Doe"


def test_entity_tracking_flow_with_container():
    """Test flow using container-based dependency resolution."""
    # Arrange - Create mock container
    mock_container = Mock()
    mock_entity_service = Mock(spec=EntityService)
    
    # Configure container to return mock service
    mock_container.get.side_effect = lambda name: {
        "entity_service": mock_entity_service,
        "entity_tracker_tool": Mock(spec=EntityTracker),
        "entity_extractor_tool": Mock(spec=EntityExtractor),
        "context_analyzer_tool": Mock(spec=ContextAnalyzer),
        "entity_resolver_tool": Mock(spec=EntityResolver),
    }.get(name)
    
    # Setup mock response
    mock_result_state = Mock(spec=EntityTrackingState)
    mock_entity_service.process_article_with_state.return_value = mock_result_state
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="Test content",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Act - Initialize flow with container
    flow = EntityTrackingFlow(container=mock_container)
    
    # Call process method - should use container to get dependencies
    result = flow.process(state)
    
    # Assert - Verify container was used to get dependencies
    mock_container.get.assert_any_call("entity_service")
    mock_entity_service.process_article_with_state.assert_called_once_with(state)
    assert result is mock_result_state


def test_entity_tracking_flow_with_mixed_dependencies():
    """Test flow with mixed explicit and container dependencies."""
    # Arrange - Create mocks and container
    mock_entity_service = Mock(spec=EntityService)
    mock_container = Mock()
    
    # Configure container to return mocks for other dependencies
    mock_container.get.side_effect = lambda name: {
        "entity_tracker_tool": Mock(spec=EntityTracker),
        "entity_extractor_tool": Mock(spec=EntityExtractor),
        "context_analyzer_tool": Mock(spec=ContextAnalyzer),
        "entity_resolver_tool": Mock(spec=EntityResolver),
    }.get(name)
    
    # Setup mock response
    mock_result_state = Mock(spec=EntityTrackingState)
    mock_entity_service.process_article_with_state.return_value = mock_result_state
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="Test content",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Act - Initialize flow with explicit entity_service and container for other deps
    flow = EntityTrackingFlow(
        container=mock_container,
        entity_service=mock_entity_service
    )
    
    # Call process method
    result = flow.process(state)
    
    # Assert - Verify explicit dependency was used
    mock_entity_service.process_article_with_state.assert_called_once_with(state)
    assert result is mock_result_state
    
    # Container should not be called for explicitly provided dependencies
    for call in mock_container.get.call_args_list:
        assert call[0][0] != "entity_service"


def test_entity_tracking_flow_handles_errors():
    """Test error handling in the flow."""
    # Arrange
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_service.process_article_with_state.side_effect = Exception("Test error")
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Create flow with mock service
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    
    # Act - The flow should catch the exception and return the state with error
    result_state = flow.process(state)
    
    # Assert
    mock_entity_service.process_article_with_state.assert_called_once_with(state)
    assert result_state.status == TrackingStatus.FAILED
    assert "Test error" in result_state.error_details.message
    assert result_state.error_details.task == "entity_processing"


def test_dependency_caching():
    """Test that dependencies are cached after being loaded."""
    # Arrange - Create mock container with tracking
    mock_container = MagicMock()
    
    # Track calls to specific dependencies
    call_counts = {}
    
    def track_gets(key):
        call_counts[key] = call_counts.get(key, 0) + 1
        if key == "entity_service":
            return Mock(spec=EntityService)
        return Mock()
    
    mock_container.get.side_effect = track_gets
    
    # Act - Create flow
    flow = EntityTrackingFlow(container=mock_container)
    
    # Access dependencies multiple times
    service1 = flow.entity_service
    service2 = flow.entity_service
    tracker1 = flow.entity_tracker
    tracker2 = flow.entity_tracker
    
    # Assert - Each dependency should only be loaded once
    assert call_counts.get("entity_service", 0) == 1
    assert call_counts.get("entity_tracker_tool", 0) == 1
    
    # Dependencies should be identical (cached)
    assert service1 is service2
    assert tracker1 is tracker2
