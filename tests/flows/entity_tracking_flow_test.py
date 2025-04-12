"""Tests for the Entity Tracking flow."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from local_newsifier.models.database import Article
from local_newsifier.models.entity_tracking import CanonicalEntity
from local_newsifier.tools.entity_tracker import EntityTracker


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    db_manager = Mock(spec=DatabaseManager)
    
    # Mock get_articles_by_status
    article1 = Article(
        id=1,
        url="https://example.com/article1",
        title="Article about Biden",
        content="Joe Biden is the president of the United States.",
        published_at=datetime.now(timezone.utc),
        status="analyzed",
        scraped_at=datetime.now(timezone.utc),
        entities=[],
        analysis_results=[]
    )
    
    article2 = Article(
        id=2,
        url="https://example.com/article2",
        title="Article about Harris",
        content="Kamala Harris is the vice president of the United States.",
        published_at=datetime.now(timezone.utc),
        status="analyzed",
        scraped_at=datetime.now(timezone.utc),
        entities=[],
        analysis_results=[]
    )
    
    db_manager.get_articles_by_status.return_value = [article1, article2]
    
    # Mock get_article
    db_manager.get_article.side_effect = lambda id: article1 if id == 1 else article2
    
    # Mock update_article_status
    db_manager.update_article_status.return_value = Mock()
    
    # Mock get_canonical_entities_by_type
    entity1 = CanonicalEntity(
        id=1,
        name="Joe Biden",
        entity_type="PERSON",
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    entity2 = CanonicalEntity(
        id=2,
        name="Kamala Harris",
        entity_type="PERSON",
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    db_manager.get_canonical_entities_by_type.return_value = [entity1, entity2]
    
    # Mock get_entity_mentions_count
    db_manager.get_entity_mentions_count.side_effect = lambda id: 5 if id == 1 else 3
    
    # Mock get_entity_timeline
    db_manager.get_entity_timeline.return_value = [
        {
            "date": datetime.now(timezone.utc),
            "context": "Joe Biden is the president.",
            "sentiment_score": 0.5,
            "article": {
                "title": "Article about Biden",
                "url": "https://example.com/article1"
            }
        }
    ]
    
    # Mock get_entity_sentiment_trend
    db_manager.get_entity_sentiment_trend.return_value = [
        {
            "date": datetime.now(timezone.utc),
            "avg_sentiment": 0.5,
            "mention_count": 3
        }
    ]
    
    return db_manager


@pytest.fixture
def mock_entity_tracker():
    """Create a mock entity tracker."""
    entity_tracker = Mock(spec=EntityTracker)
    
    # Mock process_article
    entity_tracker.process_article.return_value = [
        {
            "original_text": "Joe Biden",
            "canonical_name": "Joe Biden",
            "canonical_id": 1,
            "context": "Joe Biden is the president.",
            "sentiment_score": 0.5,
            "framing_category": "leadership"
        }
    ]
    
    # Mock get_entity_timeline
    entity_tracker.get_entity_timeline.return_value = [
        {
            "date": datetime.now(timezone.utc),
            "context": "Joe Biden is the president.",
            "sentiment_score": 0.5,
            "article": {
                "title": "Article about Biden",
                "url": "https://example.com/article1"
            }
        }
    ]
    
    # Mock get_entity_sentiment_trend
    entity_tracker.get_entity_sentiment_trend.return_value = [
        {
            "date": datetime.now(timezone.utc),
            "avg_sentiment": 0.5,
            "mention_count": 3
        }
    ]
    
    return entity_tracker


@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_init(mock_entity_tracker_class, mock_db_manager):
    """Test initializing the entity tracking flow."""
    mock_entity_tracker_class.return_value = Mock()
    
    flow = EntityTrackingFlow(mock_db_manager)
    
    mock_entity_tracker_class.assert_called_once_with(mock_db_manager)
    assert flow.db_manager is mock_db_manager
    assert flow.entity_tracker is not None


@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_process_new_articles(
    mock_entity_tracker_class, mock_db_manager, mock_entity_tracker
):
    """Test processing new articles for entity tracking."""
    mock_entity_tracker_class.return_value = mock_entity_tracker
    
    flow = EntityTrackingFlow(mock_db_manager)
    
    # Test process_new_articles
    results = flow.process_new_articles()
    
    # Verify the correct methods were called
    mock_db_manager.get_articles_by_status.assert_called_with("analyzed")
    assert mock_entity_tracker.process_article.call_count == 2
    assert mock_db_manager.update_article_status.call_count == 2
    
    # Verify the results
    assert len(results) == 2
    assert results[0]["article_id"] == 1
    assert results[0]["entity_count"] == 1
    assert results[1]["article_id"] == 2
    assert results[1]["entity_count"] == 1


@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_process_article(
    mock_entity_tracker_class, mock_db_manager, mock_entity_tracker
):
    """Test processing a single article for entity tracking."""
    mock_entity_tracker_class.return_value = mock_entity_tracker
    
    flow = EntityTrackingFlow(mock_db_manager)
    
    # Test process_article
    result = flow.process_article(1)
    
    # Verify the correct methods were called
    mock_db_manager.get_article.assert_called_with(1)
    mock_entity_tracker.process_article.assert_called_once()
    
    # Verify the result
    assert len(result) == 1
    assert result[0]["original_text"] == "Joe Biden"
    assert result[0]["canonical_name"] == "Joe Biden"
    assert result[0]["canonical_id"] == 1


@patch("local_newsifier.flows.entity_tracking_flow.EntityTracker")
def test_entity_tracking_flow_get_entity_dashboard(
    mock_entity_tracker_class, mock_db_manager, mock_entity_tracker
):
    """Test generating entity dashboard data."""
    mock_entity_tracker_class.return_value = mock_entity_tracker
    
    flow = EntityTrackingFlow(mock_db_manager)
    
    # Test get_entity_dashboard
    dashboard = flow.get_entity_dashboard(days=30, entity_type="PERSON")
    
    # Verify the correct methods were called
    mock_db_manager.get_canonical_entities_by_type.assert_called_with("PERSON")
    assert mock_db_manager.get_entity_mentions_count.call_count == 2
    assert mock_db_manager.get_entity_timeline.call_count == 2
    assert mock_db_manager.get_entity_sentiment_trend.call_count == 2
    
    # Verify the dashboard data
    assert dashboard["entity_count"] == 2
    assert dashboard["total_mentions"] == 8  # 5 + 3
    assert len(dashboard["entities"]) == 2
    assert dashboard["entities"][0]["name"] in ["Joe Biden", "Kamala Harris"]
    assert dashboard["date_range"]["days"] == 30
    assert "start" in dashboard["date_range"]
    assert "end" in dashboard["date_range"]