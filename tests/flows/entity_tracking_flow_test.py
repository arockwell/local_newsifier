"""Consolidated tests for the Entity Tracking flow."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Mock spaCy and TextBlob before imports
patch("spacy.load", MagicMock(return_value=MagicMock())).start()
patch(
    "textblob.TextBlob",
    MagicMock(return_value=MagicMock(sentiment=MagicMock(polarity=0.5, subjectivity=0.7))),
).start()
patch("spacy.language.Language", MagicMock()).start()

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.models.state import (EntityBatchTrackingState, EntityDashboardState,
                                          EntityRelationshipState, EntityTrackingState,
                                          TrackingStatus)
from local_newsifier.services.entity_service import EntityService

# ===== Initialization Tests =====


@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
@pytest.mark.parametrize(
    "init_params,expected_session",
    [
        ({}, None),  # Default initialization
        ({"session": MagicMock()}, "has_session"),  # With session
    ],
)
def test_entity_tracking_flow_init(
    mock_entity_service_class,
    mock_tracker_class,
    mock_resolver_class,
    mock_context_analyzer_class,
    mock_extractor_class,
    init_params,
    expected_session,
):
    """Test initializing the entity tracking flow with different parameters."""
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
    flow = EntityTrackingFlow(**init_params)

    # Verify service and tools were created
    assert flow.entity_service is not None
    if expected_session == "has_session":
        assert flow.session is init_params["session"]
    else:
        assert flow.session is None
    assert flow._entity_tracker is not None
    assert flow._entity_extractor is not None
    assert flow._context_analyzer is not None
    assert flow._entity_resolver is not None

    # Verify all components were created
    mock_entity_service_class.assert_called_once()
    mock_tracker_class.assert_called_once()
    mock_extractor_class.assert_called_once()
    mock_context_analyzer_class.assert_called_once()
    mock_resolver_class.assert_called_once()


@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_init_with_dependencies(
    mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class
):
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
        session=mock_session,
    )

    # Verify dependencies were used
    assert flow.entity_service is mock_entity_service
    assert flow._entity_tracker is mock_entity_tracker
    assert flow._entity_extractor is mock_entity_extractor
    assert flow._context_analyzer is mock_context_analyzer
    assert flow._entity_resolver is mock_entity_resolver
    assert flow.session is mock_session


# ===== Process Method Tests =====


@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_process_method(
    mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class
):
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
        entity_resolver=mock_entity_resolver,
    )

    # Call process method
    result = flow.process(mock_state)

    # Verify service method was called
    mock_entity_service.process_article_with_state.assert_called_once_with(mock_state)
    assert result is mock_result_state


@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_uses_service(
    mock_tracker_class,
    mock_resolver_class,
    mock_analyzer_class,
    mock_extractor_class,
    mock_service_class,
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
            "framing_category": "neutral",
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
        published_at=datetime(2025, 1, 1),
    )

    # Create flow with mock service and dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
    )

    # If the class has an async method, replace it with the mock result
    if hasattr(flow, "process_async"):
        flow.process_async = AsyncMock(return_value=mock_result_state)

    # Act - call the synchronous method
    result_state = flow.process(state)

    # Assert
    mock_service.process_article_with_state.assert_called_once_with(state)
    assert result_state is mock_result_state
    assert result_state.status == TrackingStatus.SUCCESS
    assert len(result_state.entities) == 1
    assert result_state.entities[0]["original_text"] == "John Doe"


# ===== Process New Articles Tests =====


@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_process_new_articles_method(
    mock_tracker_class, mock_resolver_class, mock_context_analyzer_class, mock_extractor_class
):
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
        entity_resolver=mock_entity_resolver,
    )

    # Call process_new_articles method
    result = flow.process_new_articles()

    # Verify service method was called with correct state
    mock_entity_service.process_articles_batch.assert_called_once()
    # Verify state passed to process_articles_batch has status_filter="analyzed"
    called_state = mock_entity_service.process_articles_batch.call_args[0][0]
    assert isinstance(called_state, EntityBatchTrackingState)
    assert called_state.status_filter == "analyzed"
    assert result is mock_result_state


# ===== Process Article Tests =====


@patch("local_newsifier.flows.entity_tracking_flow.article_crud")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
@pytest.mark.parametrize(
    "article_data,expected_entities",
    [
        (
            {
                "id": 123,
                "content": "Test content",
                "title": "Test title",
                "published_at": datetime.now(timezone.utc),
            },
            [{"entity": "test"}],
        ),
        (
            {
                "id": 1,
                "content": "Test content",
                "title": "Test article",
                "url": "http://example.com",
                "published_at": datetime.now(timezone.utc),
            },
            [{"entity_id": 1, "entity_name": "Entity"}],
        ),
    ],
)
def test_process_article_method(
    mock_tracker_class,
    mock_resolver_class,
    mock_context_analyzer_class,
    mock_extractor_class,
    mock_article_crud,
    article_data,
    expected_entities,
):
    """Test the process_article method (legacy) with parameterized inputs."""
    # Setup mocks
    mock_entity_service = Mock()  # Don't use spec to avoid attribute constraints
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()

    mock_session = Mock()
    mock_article = Mock()
    for key, value in article_data.items():
        setattr(mock_article, key, value)

    # Setup session context manager mock properly
    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_session
    mock_context_manager.__exit__.return_value = None
    mock_entity_service.session_factory.return_value = mock_context_manager

    # Configure article crud mock
    mock_article_crud.get.return_value = mock_article

    # Configure result state
    mock_result_state = Mock(spec=EntityTrackingState)
    mock_result_state.entities = expected_entities
    mock_entity_service.process_article_with_state.return_value = mock_result_state

    # Initialize flow with mock dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
    )

    # Call process_article method
    result = flow.process_article(article_id=article_data["id"])

    # Verify article was retrieved
    mock_article_crud.get.assert_called_once_with(mock_session, id=article_data["id"])

    # Verify process was called with correct state
    mock_entity_service.process_article_with_state.assert_called_once()
    called_state = mock_entity_service.process_article_with_state.call_args[0][0]
    assert isinstance(called_state, EntityTrackingState)
    assert called_state.article_id == article_data["id"]

    # Verify result
    assert result == expected_entities


# ===== Dashboard Tests =====


@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
@pytest.mark.parametrize(
    "days,entity_type,dashboard_data",
    [
        (
            30,
            "PERSON",
            {"dashboard": "data"},
        ),
        (
            30,
            "PERSON",
            {
                "entities": [
                    {"id": 1, "name": "Entity 1", "type": "PERSON", "count": 10},
                    {"id": 2, "name": "Entity 2", "type": "ORGANIZATION", "count": 5},
                ],
                "timeline": [{"date": "2023-01-01", "count": 5}],
                "sentiment_trend": [{"date": "2023-01-01", "sentiment": 0.8}],
            },
        ),
    ],
)
def test_get_entity_dashboard_method(
    mock_tracker_class,
    mock_resolver_class,
    mock_context_analyzer_class,
    mock_extractor_class,
    days,
    entity_type,
    dashboard_data,
):
    """Test the get_entity_dashboard method with different parameters."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()

    mock_result_state = Mock(spec=EntityDashboardState)
    mock_result_state.dashboard_data = dashboard_data
    mock_entity_service.generate_entity_dashboard.return_value = mock_result_state

    # Initialize flow with mock dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
    )

    # Call get_entity_dashboard method
    result = flow.get_entity_dashboard(days=days, entity_type=entity_type)

    # Verify service method was called with correct state
    mock_entity_service.generate_entity_dashboard.assert_called_once()
    called_state = mock_entity_service.generate_entity_dashboard.call_args[0][0]
    assert isinstance(called_state, EntityDashboardState)
    assert called_state.days == days
    assert called_state.entity_type == entity_type

    # Verify result
    assert result == dashboard_data


# ===== Relationship Tests =====


@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
@pytest.mark.parametrize(
    "entity_id,days,relationship_data",
    [
        (456, 15, {"relationship": "data"}),
        (
            1,
            30,
            {
                "relationships": [
                    {"source": 1, "target": 2, "weight": 5},
                    {"source": 1, "target": 3, "weight": 3},
                ],
                "entities": [
                    {"id": 1, "name": "Entity 1"},
                    {"id": 2, "name": "Entity 2"},
                    {"id": 3, "name": "Entity 3"},
                ],
            },
        ),
    ],
)
def test_find_entity_relationships_method(
    mock_tracker_class,
    mock_resolver_class,
    mock_context_analyzer_class,
    mock_extractor_class,
    entity_id,
    days,
    relationship_data,
):
    """Test the find_entity_relationships method with different parameters."""
    # Setup mocks
    mock_entity_service = Mock(spec=EntityService)
    mock_entity_tracker = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()

    mock_result_state = Mock(spec=EntityRelationshipState)
    mock_result_state.relationship_data = relationship_data
    mock_entity_service.find_entity_relationships.return_value = mock_result_state

    # Initialize flow with mock dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
    )

    # Call find_entity_relationships method
    result = flow.find_entity_relationships(entity_id=entity_id, days=days)

    # Verify service method was called with correct state
    mock_entity_service.find_entity_relationships.assert_called_once()
    called_state = mock_entity_service.find_entity_relationships.call_args[0][0]
    assert isinstance(called_state, EntityRelationshipState)
    assert called_state.entity_id == entity_id
    assert called_state.days == days

    # Verify result
    assert result == relationship_data


# ===== Error Handling Tests =====


@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_handles_errors(
    mock_tracker_class,
    mock_resolver_class,
    mock_analyzer_class,
    mock_extractor_class,
    mock_service_class,
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
        published_at=datetime(2025, 1, 1),
    )

    # Create flow with mock service and dependencies to avoid loading spaCy models
    flow = EntityTrackingFlow(
        entity_service=mock_service,
        entity_tracker=mock_entity_tracker,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
    )

    # If the class has an async method, make sure it doesn't interfere with our test
    if hasattr(flow, "process_async"):
        # Set it to a mock that won't be called (we're testing the sync path)
        flow.process_async = AsyncMock()

    # Act - The flow should catch the exception and return the state with error
    result_state = flow.process(state)

    # Assert
    mock_service.process_article_with_state.assert_called_once_with(state)
    assert result_state.status == TrackingStatus.FAILED
    assert "Test error" in result_state.error_details.message
    assert result_state.error_details.task == "entity_processing"


# ===== State Logging Tests =====


def test_entity_tracking_state_logs():
    """Test that logs are properly added to EntityTrackingState."""
    # Create state
    state = EntityTrackingState(
        article_id=1,
        content="Test content",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Add some logs
    state.add_log("Test log 1")
    state.add_log("Test log 2")

    # Verify logs
    assert len(state.run_logs) == 2
    assert "Test log 1" in state.run_logs[0]
    assert "Test log 2" in state.run_logs[1]
    assert "[" in state.run_logs[0]  # Should have timestamp
