"""Tests for the EntityTrackingFlow state-based implementation."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock spaCy and TextBlob before imports
patch('spacy.load', MagicMock(return_value=MagicMock())).start()
patch('textblob.TextBlob', MagicMock(return_value=MagicMock(
    sentiment=MagicMock(polarity=0.5, subjectivity=0.7)
))).start()
patch('spacy.language.Language', MagicMock()).start()

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlowBase
from local_newsifier.models.state import EntityTrackingState, TrackingStatus
from local_newsifier.services.entity_service import EntityService
from tests.ci_skip_config import ci_skip
from tests.fixtures.event_loop import event_loop_fixture


@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_uses_service(
    mock_tracker_class, mock_resolver_class, mock_analyzer_class, 
    mock_extractor_class, mock_service_class
):
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
    mock_service_class.return_value = mock_service
    
    # Create mocks for required components
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer
    
    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver
    
    mock_tracker = MagicMock()
    mock_tracker_class.return_value = mock_tracker
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )

    # Create flow with mock service and dependencies to avoid loading spaCy models
    flow = EntityTrackingFlowBase(
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
    # Setup mocks
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer
    
    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver
    
    mock_tracker = MagicMock()
    mock_tracker_class.return_value = mock_tracker
    
    # Create flow without providing a service
    flow = EntityTrackingFlowBase()
    
    # Verify the service and tools were created
    mock_service_class.assert_called_once()
    mock_extractor_class.assert_called_once()
    mock_analyzer_class.assert_called_once()
    mock_resolver_class.assert_called_once()
    mock_tracker_class.assert_called_once()
    
    assert flow.entity_service is mock_service
    assert flow._entity_extractor is mock_extractor
    assert flow._context_analyzer is mock_analyzer
    assert flow._entity_resolver is mock_resolver
    assert flow._entity_tracker is mock_tracker


@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_handles_errors(
    mock_tracker_class, mock_resolver_class, mock_analyzer_class, 
    mock_extractor_class, mock_service_class
):
    """Test that EntityTrackingFlow properly handles errors during processing."""
    # Arrange
    mock_service = MagicMock(spec=EntityService)
    mock_entity_tracker = MagicMock()
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    mock_service.process_article_with_state.side_effect = Exception("Test error")
    mock_service_class.return_value = mock_service
    
    # Create mocks for required components
    mock_extractor = MagicMock()
    mock_extractor_class.return_value = mock_extractor
    
    mock_analyzer = MagicMock()
    mock_analyzer_class.return_value = mock_analyzer
    
    mock_resolver = MagicMock()
    mock_resolver_class.return_value = mock_resolver
    
    mock_tracker = MagicMock()
    mock_tracker_class.return_value = mock_tracker
    
    # Create test state
    state = EntityTrackingState(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Create flow with mock service and dependencies to avoid loading spaCy models
    flow = EntityTrackingFlowBase(
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
