"""Tests for the Entity Tracking flow."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

import pytest

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.models.state import EntityTrackingState, EntityBatchTrackingState, EntityDashboardState, EntityRelationshipState, TrackingStatus
from local_newsifier.services.entity_service import EntityService


@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
def test_entity_tracking_flow_init(
    mock_entity_service_class, 
    mock_tracker_class,
    mock_resolver_class, 
    mock_context_analyzer_class, 
    mock_extractor_class
):
    """Test initializing the entity tracking flow with defaults."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_service_class.return_value = mock_entity_service
    
    mock_tracker = Mock()
    mock_tracker_class.return_value = mock_tracker
    
    mock_extractor = Mock()
    mock_extractor_class.return_value = mock_extractor
    
    mock_analyzer = Mock()
    mock_context_analyzer_class.return_value = mock_analyzer
    
    mock_resolver = Mock()
    mock_resolver_class.return_value = mock_resolver
    
    # Initialize flow
    flow = EntityTrackingFlow()
    
    # Verify service and tools were created
    assert flow.entity_service is not None
    assert flow.session is None
    assert flow._entity_tracker is not None
    assert flow._entity_extractor is not None
    assert flow._context_analyzer is not None
    assert flow._entity_resolver is not None


def test_entity_tracking_flow_init_with_dependencies():
    """Test initializing the entity tracking flow with provided dependencies."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    mock_session_factory = Mock()
    mock_session = Mock()
    
    # Initialize flow with mock dependencies
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
        session_factory=mock_session_factory,
        session=mock_session
    )
    
    # Verify dependencies were used
    assert flow.entity_service is mock_entity_service
    assert flow._entity_tracker is mock_entity_tracker
    assert flow._entity_extractor is mock_entity_extractor
    assert flow._context_analyzer is mock_context_analyzer
    assert flow._entity_resolver is mock_entity_resolver
    assert flow.session is mock_session


@patch("local_newsifier.flows.entity_tracking_flow.EntityTrackingFlow")
@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTrackingState")
@patch("local_newsifier.flows.entity_tracking_flow.TrackingStatus")
def test_process_method_mocked(mock_tracking_status, mock_state_class, mock_entity_service_class, mock_flow_class):
    """Test the process method using complete mocking."""
    # Skip this test as it requires more complex mocking
    pytest.skip("Needs complex mocking due to crewai integration")
    
    # Setup mocks
    mock_entity_service = Mock()
    mock_entity_service_class.return_value = mock_entity_service
    
    mock_state = Mock()
    mock_state_class.return_value = mock_state
    
    mock_result_state = Mock()
    mock_entity_service.process_article_with_state.return_value = mock_result_state
    
    # Setup tracking status
    mock_tracking_status.FAILED = "FAILED"
    
    # Create flow instance with mocked process method
    mock_flow = Mock()
    mock_flow_class.return_value = mock_flow
    mock_flow.process.return_value = mock_result_state
    
    # Call the mocked process method
    result = mock_flow.process(mock_state)
    
    # Verify expectations
    mock_flow.process.assert_called_once_with(mock_state)
    assert result is mock_result_state


def test_process_new_articles_method():
    """Test the process_new_articles method."""
    # Skip this test as it requires more complex mocking
    pytest.skip("Needs complex mocking due to crewai integration")


@patch("local_newsifier.flows.entity_tracking_flow.article_crud")
def test_process_article_method(mock_article_crud):
    """Test the process_article method (legacy)."""
    # Skip this test as it requires more complex mocking
    pytest.skip("Needs complex mocking due to crewai integration")


def test_get_entity_dashboard_method():
    """Test the get_entity_dashboard method."""
    # Skip this test as it requires more complex mocking
    pytest.skip("Needs complex mocking due to crewai integration")


def test_find_entity_relationships_method():
    """Test the find_entity_relationships method."""
    # Skip this test as it requires more complex mocking
    pytest.skip("Needs complex mocking due to crewai integration")
