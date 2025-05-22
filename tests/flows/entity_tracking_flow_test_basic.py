"""Basic tests for the Entity Tracking flow."""

from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone, timedelta

import pytest

# Mock spaCy and TextBlob before imports
patch("spacy.load", MagicMock(return_value=MagicMock())).start()
patch(
    "textblob.TextBlob",
    MagicMock(return_value=MagicMock(sentiment=MagicMock(polarity=0.5, subjectivity=0.7))),
).start()
patch("spacy.language.Language", MagicMock()).start()

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow


@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
@patch("local_newsifier.flows.entity_tracking_flow.EntityExtractor")
@patch("local_newsifier.flows.entity_tracking_flow.ContextAnalyzer")
@patch("local_newsifier.flows.entity_tracking_flow.EntityResolver")
@patch("local_newsifier.flows.entity_tracking_flow.EntityService")
def test_entity_tracking_flow_init_basic(
    mock_entity_service_class,
    mock_entity_resolver_class,
    mock_context_analyzer_class,
    mock_entity_extractor_class,
    mock_entity_tracker_class,
):
    """Test initializing the entity tracking flow."""
    # Setup mocks
    mock_tracker = Mock()
    mock_entity_tracker_class.return_value = mock_tracker

    mock_service = Mock()
    mock_entity_service_class.return_value = mock_service

    # Test with session and without session
    flow1 = EntityTrackingFlow()
    flow2 = EntityTrackingFlow(session=MagicMock())

    assert flow1._entity_tracker is not None
    assert flow2._entity_tracker is not None
    assert mock_entity_tracker_class.call_count == 2


@patch("local_newsifier.flows.entity_tracking_flow.article_crud")
def test_process_article_basic(mock_article_crud):
    """Test process_article method with mocked service."""
    # Setup mocks to bypass session handling
    mock_session = MagicMock()
    mock_article = MagicMock(
        id=1, title="Test article", content="Test content", url="http://example.com"
    )
    mock_article.published_at = datetime.now(timezone.utc)
    mock_article_crud.get.return_value = mock_article

    # Mock the entity service
    mock_entity_service = Mock()
    mock_result_state = Mock()
    mock_result_state.entities = [{"entity_id": 1, "entity_name": "Entity"}]
    mock_entity_service.process_article_with_state.return_value = mock_result_state

    # Setup session factory
    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_session
    mock_context_manager.__exit__.return_value = None
    mock_entity_service.session_factory.return_value = mock_context_manager

    # Test process_article
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    result = flow.process_article(article_id=1)

    # Basic assertions
    assert isinstance(result, list)
    mock_article_crud.get.assert_called_once()
    mock_entity_service.process_article_with_state.assert_called_once()


def test_get_entity_dashboard_basic():
    """Test get_entity_dashboard with mocked service."""
    # Setup mocks
    mock_entity_service = Mock()
    mock_result_state = Mock()
    mock_result_state.dashboard_data = {
        "entities": [
            {"id": 1, "name": "Entity 1", "type": "PERSON", "count": 10},
            {"id": 2, "name": "Entity 2", "type": "ORGANIZATION", "count": 5},
        ],
        "timeline": [{"date": "2023-01-01", "count": 5}],
        "sentiment_trend": [{"date": "2023-01-01", "sentiment": 0.8}],
    }
    mock_entity_service.generate_entity_dashboard.return_value = mock_result_state

    # Test get_entity_dashboard
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    result = flow.get_entity_dashboard(entity_type="PERSON", days=30)

    # Basic assertions
    assert isinstance(result, dict)
    assert "entities" in result
    mock_entity_service.generate_entity_dashboard.assert_called_once()


def test_process_new_articles_basic():
    """Test process_new_articles with mocked service."""
    # Setup mocks
    mock_entity_service = Mock()
    mock_result_state = Mock()
    mock_result_state.articles_processed = 2
    mock_result_state.entities_found = 5
    mock_entity_service.process_articles_batch.return_value = mock_result_state

    # Test process_new_articles
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    result = flow.process_new_articles()

    # Basic assertions
    assert result is mock_result_state
    mock_entity_service.process_articles_batch.assert_called_once()
    # Verify the parameter is a BatchTrackingState with status_filter="analyzed"
    args, _ = mock_entity_service.process_articles_batch.call_args
    assert args[0].status_filter == "analyzed"


def test_find_entity_relationships_basic():
    """Test find_entity_relationships with mocked service."""
    # Setup mocks
    mock_entity_service = Mock()
    mock_result_state = Mock()
    mock_result_state.relationship_data = {
        "relationships": [
            {"source": 1, "target": 2, "weight": 5},
            {"source": 1, "target": 3, "weight": 3},
        ],
        "entities": [
            {"id": 1, "name": "Entity 1"},
            {"id": 2, "name": "Entity 2"},
            {"id": 3, "name": "Entity 3"},
        ],
    }
    mock_entity_service.find_entity_relationships.return_value = mock_result_state

    # Test find_entity_relationships
    flow = EntityTrackingFlow(entity_service=mock_entity_service)
    result = flow.find_entity_relationships(entity_id=1, days=30)

    # Basic assertions
    assert result is mock_result_state.relationship_data
    mock_entity_service.find_entity_relationships.assert_called_once()
    # Verify the parameter is a RelationshipState with the correct entity_id and days
    args, _ = mock_entity_service.find_entity_relationships.call_args
    assert args[0].entity_id == 1
    assert args[0].days == 30
