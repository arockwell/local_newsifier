"""Basic tests for the Entity Tracking flow."""

from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone, timedelta

import pytest

from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow


@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_init_basic(mock_entity_tracker_class):
    """Test initializing the entity tracking flow."""
    mock_tracker = Mock()
    mock_entity_tracker_class.return_value = mock_tracker
    
    # Test with session and without session
    flow1 = EntityTrackingFlow()
    flow2 = EntityTrackingFlow(session=MagicMock())
    
    assert flow1.entity_tracker is not None
    assert flow2.entity_tracker is not None
    assert mock_entity_tracker_class.call_count == 2


@patch("local_newsifier.database.engine.with_session")
@patch("local_newsifier.flows.entity_tracking_flow.article_crud")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_process_article_basic(mock_tracker_class, mock_article_crud, mock_with_session):
    """Test process_article method with mocked session handling."""
    # Setup mocks to bypass session handling
    mock_session = MagicMock()
    mock_article = MagicMock(id=1, title="Test article", url="http://example.com")
    mock_article_crud.get.return_value = mock_article
    
    # Mock the entity tracker to return entities
    mock_tracker = Mock()
    mock_tracker.track_entities.return_value = [{"entity_id": 1, "entity_name": "Entity"}]
    mock_tracker_class.return_value = mock_tracker
    
    # Mock with_session to simply call the function with the mock session
    mock_with_session.side_effect = lambda f: lambda *args, **kwargs: f(*args, session=mock_session, **kwargs)
    
    # Test process_article
    flow = EntityTrackingFlow(session=mock_session)
    result = flow.process_article(article_id=1)
    
    # Basic assertions
    assert isinstance(result, list)
    mock_article_crud.get.assert_called_once()
    mock_tracker.track_entities.assert_called_once()


@patch("local_newsifier.database.engine.with_session")
@patch("local_newsifier.flows.entity_tracking_flow.canonical_entity_crud")
@patch("local_newsifier.flows.entity_tracking_flow.entity_mention_context_crud")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_get_entity_dashboard_basic(mock_tracker_class, mock_context_crud, mock_canonical_crud, mock_with_session):
    """Test get_entity_dashboard with mocked session handling."""
    # Setup mocks
    mock_session = MagicMock()
    mock_entity1 = MagicMock(id=1, name="Entity 1", entity_type="PERSON")
    mock_entity2 = MagicMock(id=2, name="Entity 2", entity_type="ORGANIZATION")
    mock_canonical_crud.get_all.return_value = [mock_entity1, mock_entity2]
    
    # Mock timeline and sentiment data
    mock_context_crud.get_timeline.return_value = [{"date": "2023-01-01", "count": 5}]
    mock_context_crud.get_sentiment_trend.return_value = [{"date": "2023-01-01", "sentiment": 0.8}]
    
    # Mock with_session to simply call the function with the mock session
    mock_with_session.side_effect = lambda f: lambda *args, **kwargs: f(*args, session=mock_session, **kwargs)
    
    # Test get_entity_dashboard
    flow = EntityTrackingFlow(session=mock_session)
    result = flow.get_entity_dashboard(entity_type="PERSON", days=30)
    
    # Basic assertions
    assert isinstance(result, dict)
    assert "entities" in result
    mock_canonical_crud.get_all.assert_called_once()
    assert mock_context_crud.get_timeline.call_count > 0
    assert mock_context_crud.get_sentiment_trend.call_count > 0


@patch("local_newsifier.database.engine.with_session")
@patch("local_newsifier.flows.entity_tracking_flow.article_crud")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_process_new_articles_basic(mock_tracker_class, mock_article_crud, mock_with_session):
    """Test process_new_articles with mocked session handling."""
    # Setup mocks
    mock_session = MagicMock()
    mock_article1 = MagicMock(id=1, title="Article 1", url="http://example.com/1")
    mock_article2 = MagicMock(id=2, title="Article 2", url="http://example.com/2")
    mock_article_crud.get_by_status.return_value = [mock_article1, mock_article2]
    
    # Mock the entity tracker to return entities
    mock_tracker = Mock()
    mock_tracker.track_entities.return_value = [{"entity_id": 1, "entity_name": "Entity"}]
    mock_tracker_class.return_value = mock_tracker
    
    # Mock with_session to simply call the function with the mock session
    mock_with_session.side_effect = lambda f: lambda *args, **kwargs: f(*args, session=mock_session, **kwargs)
    
    # Create a flow with mocked process_article method
    flow = EntityTrackingFlow(session=mock_session)
    with patch.object(flow, 'process_article') as mock_process_article:
        mock_process_article.return_value = [{"entity_id": 1, "entity_name": "Entity"}]
        
        # Test process_new_articles
        results = flow.process_new_articles(session=mock_session)
        
        # Basic assertions
        assert isinstance(results, list)
        assert len(results) == 2
        mock_article_crud.get_by_status.assert_called_once_with(mock_session, status="analyzed")
        assert mock_process_article.call_count == 2
        mock_article_crud.update_status.assert_has_calls([
            call(mock_session, article_id=1, status="entity_tracked"),
            call(mock_session, article_id=2, status="entity_tracked")
        ])


@patch("local_newsifier.database.engine.with_session")
@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_find_entity_relationships_basic(mock_tracker_class, mock_with_session):
    """Test find_entity_relationships with mocked session handling."""
    # Setup mocks
    mock_session = MagicMock()
    mock_tracker = Mock()
    mock_tracker.find_co_occurrences.return_value = {"relationships": [], "entities_processed": 5}
    mock_tracker_class.return_value = mock_tracker
    
    # Mock with_session to use the parameter method correctly - important for this test
    def side_effect(f):
        def wrapper(*args, **kwargs):
            if 'min_occurrences' in kwargs:
                min_occ = kwargs.pop('min_occurrences')
                return f(*args, session=mock_session, min_occurrences=min_occ, **kwargs)
            return f(*args, session=mock_session, **kwargs)
        return wrapper
    
    mock_with_session.side_effect = side_effect
    
    # Test find_entity_relationships
    flow = EntityTrackingFlow(session=mock_session)
    result = flow.find_entity_relationships(entity_id=1, min_occurrences=2)
    
    # Basic assertions
    assert isinstance(result, dict)
    mock_tracker.find_co_occurrences.assert_called_once_with(min_occurrences=2)
