"""Tests for the improved EntityTrackingFlow implementation."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from local_newsifier.flows.entity_tracking_flow_improved import EntityTrackingFlow
from local_newsifier.models.state import EntityTrackingState, TrackingStatus
from local_newsifier.services.entity_service import EntityService


def test_entity_tracking_flow_with_explicit_dependencies():
    """Test EntityTrackingFlow with explicitly provided dependencies."""
    # Arrange - Create mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    
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


def test_entity_tracking_flow_with_lazy_resolution():
    """Test EntityTrackingFlow with lazy dependency resolution via container."""
    # Arrange - Create mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_container = Mock()
    mock_container.get.side_effect = lambda name: {
        "entity_service": mock_entity_service,
        "entity_tracker_tool": Mock(),
        "entity_extractor_tool": Mock(),
        "context_analyzer_tool": Mock(),
        "entity_resolver_tool": Mock(),
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


def test_entity_tracking_flow_handles_errors():
    """Test that EntityTrackingFlow properly handles errors during processing."""
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


def test_flow_dependency_initialization():
    """Test how flow initializes dependencies properly."""
    # Test that flow creates service if direct dependencies are available
    mock_extractor = Mock()
    mock_analyzer = Mock()
    mock_resolver = Mock()
    mock_session_factory = Mock()
    
    # No entity_service provided
    flow = EntityTrackingFlow(
        entity_extractor=mock_extractor,
        context_analyzer=mock_analyzer,
        entity_resolver=mock_resolver,
        session_factory=mock_session_factory
    )
    
    # Should have created entity_service
    assert flow.entity_service is not None
    
    # Test with partial dependencies and container fallback
    mock_container = Mock()
    mock_service = Mock(spec=EntityService)
    mock_container.get.side_effect = lambda name: {
        "entity_service": mock_service,
    }.get(name)
    
    flow = EntityTrackingFlow(
        entity_extractor=mock_extractor,  # Directly provided
        container=mock_container  # Other deps from container
    )
    
    # Should use container for service
    assert flow.entity_service is mock_service
    
    # Other dependencies should be looked up from container when needed
    flow.process_new_articles()
    mock_container.get.assert_any_call("entity_service")
