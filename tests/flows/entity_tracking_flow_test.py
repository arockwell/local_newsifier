"""Tests for the Entity Tracking flow."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi import Depends
from sqlmodel import Session

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlowBase as EntityTrackingFlow
from local_newsifier.models.state import EntityTrackingState, EntityBatchTrackingState, EntityDashboardState, EntityRelationshipState, TrackingStatus
from local_newsifier.services.entity_service import EntityService
from local_newsifier.tools.entity_tracker_service import EntityTracker


def test_entity_tracking_flow_init_with_di():
    """Test initializing the entity tracking flow with dependency injection."""
    # Setup direct mocks 
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock(spec=EntityTracker)
    mock_session = Mock(spec=Session)
    
    # Directly create a flow instance with mocked dependencies
    # In tests we're using the EntityTrackingFlowBase directly 
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        session=mock_session
    )
    
    # Verify dependencies were set correctly
    assert flow.entity_service is mock_entity_service
    assert flow._entity_tracker is mock_entity_tracker
    assert flow.session is mock_session


def test_entity_tracking_flow_init_with_explicit_dependencies():
    """Test initializing the entity tracking flow with explicitly provided dependencies."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock(spec=EntityTracker)
    mock_session = Mock(spec=Session)
    mock_session_factory = Mock()
    
    # Initialize flow with explicit dependencies
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        session=mock_session,
        session_factory=mock_session_factory
    )
    
    # Verify dependencies were used
    assert flow.entity_service is mock_entity_service
    assert flow._entity_tracker is mock_entity_tracker
    assert flow.session is mock_session
    assert flow._session_factory is mock_session_factory


def test_process_method():
    """Test the process method."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_state = Mock(spec=EntityTrackingState)
    mock_result_state = Mock(spec=EntityTrackingState)
    mock_entity_service.process_article_with_state.return_value = mock_result_state
    
    # Initialize flow
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    
    # Call process method
    result = flow.process(mock_state)
    
    # Verify service method was called
    mock_entity_service.process_article_with_state.assert_called_once_with(mock_state)
    assert result is mock_result_state


def test_process_new_articles_method():
    """Test the process_new_articles method."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_result_state = Mock(spec=EntityBatchTrackingState)
    mock_entity_service.process_articles_batch.return_value = mock_result_state
    
    # Initialize flow
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    
    # Call process_new_articles method
    result = flow.process_new_articles()
    
    # Verify service method was called with correct state
    mock_entity_service.process_articles_batch.assert_called_once()
    # Verify the state passed to process_articles_batch is EntityBatchTrackingState with status_filter="analyzed"
    called_state = mock_entity_service.process_articles_batch.call_args[0][0]
    assert isinstance(called_state, EntityBatchTrackingState)
    assert called_state.status_filter == "analyzed"
    assert result is mock_result_state


@patch("local_newsifier.flows.entity_tracking_flow.article_crud")
def test_process_article_method(mock_article_crud):
    """Test the process_article method (legacy)."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_session = Mock()
    mock_article = Mock()
    mock_article.id = 123
    mock_article.content = "Test content"
    mock_article.title = "Test title"
    mock_article.published_at = datetime.now(timezone.utc)
    
    # Setup session context manager mock properly
    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_session
    mock_context_manager.__exit__.return_value = None
    
    # Setup session factory mock
    mock_session_factory = Mock(return_value=mock_context_manager)
    
    # Configure article crud mock
    mock_article_crud.get.return_value = mock_article
    
    # Configure result state
    mock_result_state = Mock(spec=EntityTrackingState)
    mock_result_state.entities = [{"entity": "test"}]
    mock_entity_service.process_article_with_state.return_value = mock_result_state
    
    # Initialize flow with session factory
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        session_factory=mock_session_factory
    )
    
    # Call process_article method
    result = flow.process_article(article_id=123)
    
    # Verify session factory was called
    mock_session_factory.assert_called_once()
    
    # Verify article was retrieved
    mock_article_crud.get.assert_called_once_with(mock_session, id=123)
    
    # Verify process was called with correct state
    mock_entity_service.process_article_with_state.assert_called_once()
    called_state = mock_entity_service.process_article_with_state.call_args[0][0]
    assert isinstance(called_state, EntityTrackingState)
    assert called_state.article_id == 123
    
    # Verify result
    assert result == [{"entity": "test"}]


def test_get_entity_dashboard_method():
    """Test the get_entity_dashboard method."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_result_state = Mock(spec=EntityDashboardState)
    mock_result_state.dashboard_data = {"dashboard": "data"}
    mock_entity_service.generate_entity_dashboard.return_value = mock_result_state
    
    # Initialize flow
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    
    # Call get_entity_dashboard method
    result = flow.get_entity_dashboard(days=30, entity_type="PERSON")
    
    # Verify service method was called with correct state
    mock_entity_service.generate_entity_dashboard.assert_called_once()
    called_state = mock_entity_service.generate_entity_dashboard.call_args[0][0]
    assert isinstance(called_state, EntityDashboardState)
    assert called_state.days == 30
    assert called_state.entity_type == "PERSON"
    
    # Verify result
    assert result == {"dashboard": "data"}


def test_find_entity_relationships_method():
    """Test the find_entity_relationships method."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_result_state = Mock(spec=EntityRelationshipState)
    mock_result_state.relationship_data = {"relationship": "data"}
    mock_entity_service.find_entity_relationships.return_value = mock_result_state
    
    # Initialize flow
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    
    # Call find_entity_relationships method
    result = flow.find_entity_relationships(entity_id=456, days=15)
    
    # Verify service method was called with correct state
    mock_entity_service.find_entity_relationships.assert_called_once()
    called_state = mock_entity_service.find_entity_relationships.call_args[0][0]
    assert isinstance(called_state, EntityRelationshipState)
    assert called_state.entity_id == 456
    assert called_state.days == 15
    
    # Verify result
    assert result == {"relationship": "data"}
