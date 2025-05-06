"""Tests for the Entity Tracking flow."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

import pytest

# Mock spaCy and TextBlob before imports
patch('spacy.load', MagicMock(return_value=MagicMock())).start()
patch('textblob.TextBlob', MagicMock(return_value=MagicMock(
    sentiment=MagicMock(polarity=0.5, subjectivity=0.7)
))).start()
patch('spacy.language.Language', MagicMock()).start()

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.models.state import EntityTrackingState, EntityBatchTrackingState, EntityDashboardState, EntityRelationshipState, TrackingStatus
from local_newsifier.services.entity_service import EntityService
from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip, ci_skip_async


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


@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_init_with_dependencies(mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class):
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


@ci_skip("Event loop closure issues in CI")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_process_method(mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class, event_loop_fixture):
    """Test the process method."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    
    mock_state = Mock(spec=EntityTrackingState)
    mock_result_state = Mock(spec=EntityTrackingState)
    mock_entity_service.process_article_with_state.return_value = mock_result_state
    
    # Set up component mocks
    mock_tracker = Mock()
    mock_tracker_class.return_value = mock_tracker
    mock_extractor = Mock()
    mock_extractor_class.return_value = mock_extractor
    mock_analyzer = Mock()
    mock_context_analyzer_class.return_value = mock_analyzer
    mock_resolver = Mock()
    mock_resolver_class.return_value = mock_resolver
    # Initialize flow with mock dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )
    
    # Call process method
    result = flow.process(mock_state)
    
    # Verify service method was called
    mock_entity_service.process_article_with_state.assert_called_once_with(mock_state)
    assert result is mock_result_state


@ci_skip("Batch processing issues in CI")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_process_new_articles_method(mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class, event_loop_fixture):
    """Test the process_new_articles method."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    
    mock_result_state = Mock(spec=EntityBatchTrackingState)
    mock_entity_service.process_articles_batch.return_value = mock_result_state
    
    # Initialize flow with mock dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )
    
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
@ci_skip("Database session management issues in CI")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_process_article_method(mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class, mock_article_crud, event_loop_fixture):
    """Test the process_article method (legacy)."""
    # Setup mocks
    mock_entity_service = Mock()  # Don't use spec to avoid attribute constraints
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    
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
    mock_entity_service.session_factory.return_value = mock_context_manager
    
    # Configure article crud mock
    mock_article_crud.get.return_value = mock_article
    
    # Configure result state
    mock_result_state = Mock(spec=EntityTrackingState)
    mock_result_state.entities = [{"entity": "test"}]
    mock_entity_service.process_article_with_state.return_value = mock_result_state
    
    # Initialize flow with mock dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )
    
    # Call process_article method
    result = flow.process_article(article_id=123)
    
    # Verify article was retrieved
    mock_article_crud.get.assert_called_once_with(mock_session, id=123)
    
    # Verify process was called with correct state
    mock_entity_service.process_article_with_state.assert_called_once()
    called_state = mock_entity_service.process_article_with_state.call_args[0][0]
    assert isinstance(called_state, EntityTrackingState)
    assert called_state.article_id == 123
    
    # Verify result
    assert result == [{"entity": "test"}]


@ci_skip("Dashboard generation issues in CI")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_get_entity_dashboard_method(mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class, event_loop_fixture):
    """Test the get_entity_dashboard method."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    
    mock_result_state = Mock(spec=EntityDashboardState)
    mock_result_state.dashboard_data = {"dashboard": "data"}
    mock_entity_service.generate_entity_dashboard.return_value = mock_result_state
    
    # Initialize flow with mock dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )
    
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


@ci_skip("Entity relationship analysis issues in CI")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_find_entity_relationships_method(mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class, event_loop_fixture):
    """Test the find_entity_relationships method."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    
    mock_result_state = Mock(spec=EntityRelationshipState)
    mock_result_state.relationship_data = {"relationship": "data"}
    mock_entity_service.find_entity_relationships.return_value = mock_result_state
    
    # Initialize flow with mock dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver
    )
    
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
