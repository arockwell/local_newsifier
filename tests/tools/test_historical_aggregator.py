"""Tests for the HistoricalDataAggregator tool."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select

from local_newsifier.models import Article, Entity
from local_newsifier.models.trend import TimeFrame, TopicFrequency
from local_newsifier.tools.historical_aggregator import HistoricalDataAggregator


@pytest.fixture
def mock_session():
    """Fixture for a mocked SQLModel Session."""
    mock_session = MagicMock(spec=Session)
    return mock_session

@pytest.fixture(autouse=True)
def mock_database_config():
    """Fixture to mock database config functions."""
    with patch("local_newsifier.tools.historical_aggregator.get_database_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        mock_settings.return_value.DATABASE_URL = "sqlite:///:memory:"
        yield mock_settings


@pytest.fixture
def sample_articles():
    """Fixture providing sample article data."""
    now = datetime.now(timezone.utc)
    return [
        Article(
            id=1,
            url="https://example.com/news/article1",
            title="Mayor Johnson announces new development",
            source="Example News",
            published_at=now - timedelta(days=5),
            content="Article content about Mayor Johnson...",
            status="analyzed",
            scraped_at=now - timedelta(days=5),
        ),
        Article(
            id=2,
            url="https://example.com/news/article2",
            title="City Council approves downtown project",
            source="Example News",
            published_at=now - timedelta(days=3),
            content="Article content about City Council...",
            status="analyzed",
            scraped_at=now - timedelta(days=3),
        ),
        Article(
            id=3,
            url="https://example.com/news/article3",
            title="Local businesses react to new development",
            source="Example News",
            published_at=now - timedelta(days=1),
            content="Article content about local businesses...",
            status="analyzed",
            scraped_at=now - timedelta(days=1),
        ),
    ]


@pytest.fixture
def sample_entities():
    """Fixture providing sample entity data."""
    return [
        Entity(id=1, article_id=1, text="Mayor Johnson", entity_type="PERSON", confidence=0.9),
        Entity(id=2, article_id=1, text="City Hall", entity_type="ORG", confidence=0.85),
        Entity(id=3, article_id=2, text="City Council", entity_type="ORG", confidence=0.95),
        Entity(id=4, article_id=2, text="Downtown Project", entity_type="ORG", confidence=0.9),
        Entity(id=5, article_id=3, text="Downtown Project", entity_type="ORG", confidence=0.9),
        Entity(id=6, article_id=3, text="Local Businesses", entity_type="ORG", confidence=0.8),
    ]


def test_init(mock_session):
    """Test HistoricalDataAggregator initialization."""
    with patch("local_newsifier.tools.historical_aggregator.init_db") as mock_init_db, \
         patch("local_newsifier.tools.historical_aggregator.Session") as mock_session_cls:
        
        mock_engine = MagicMock()
        mock_init_db.return_value = mock_engine
        mock_session_cls.return_value = mock_session
        
        # Test with default initialization
        aggregator = HistoricalDataAggregator()
        assert aggregator._cache == {}
        mock_init_db.assert_called_once()
        
        # Test with provided session
        aggregator = HistoricalDataAggregator(session=mock_session)
        assert aggregator.session == mock_session


def test_get_articles_in_timeframe(mock_session, sample_articles):
    """Test retrieving articles within a timeframe."""
    # Setup
    mock_session.exec.return_value.all.side_effect = [sample_articles, []]
    
    aggregator = HistoricalDataAggregator(session=mock_session)
    
    # Test without source filter
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    end_date = datetime.now(timezone.utc)
    
    result = aggregator.get_articles_in_timeframe(start_date, end_date)
    
    assert result == sample_articles
    mock_session.exec.assert_called()
    
    # Test with source filter
    result = aggregator.get_articles_in_timeframe(start_date, end_date, source="Example News")
    
    assert result == []  # Mocked to return empty for source filter
    mock_session.exec.assert_called()


def test_calculate_date_range(mock_session):
    """Test date range calculation for different time frames."""
    aggregator = HistoricalDataAggregator(session=mock_session)
    
    # Test DAY time frame
    start, end = aggregator.calculate_date_range(TimeFrame.DAY, 7)
    assert (end - start).days == 7
    
    # Test WEEK time frame
    start, end = aggregator.calculate_date_range(TimeFrame.WEEK, 4)
    assert (end - start).days == 28  # 4 weeks
    
    # Test MONTH time frame
    start, end = aggregator.calculate_date_range(TimeFrame.MONTH, 2)
    assert (end - start).days == 60  # Approximately 2 months (30 days each)
    
    # Test QUARTER time frame
    start, end = aggregator.calculate_date_range(TimeFrame.QUARTER, 1)
    assert (end - start).days == 90  # Approximately 1 quarter (90 days)
    
    # Test YEAR time frame
    start, end = aggregator.calculate_date_range(TimeFrame.YEAR, 1)
    assert (end - start).days == 365  # Approximately 1 year
    
    # Test invalid time frame
    with pytest.raises(ValueError):
        aggregator.calculate_date_range("INVALID", 1)


@patch("local_newsifier.tools.historical_aggregator.HistoricalDataAggregator.get_articles_in_timeframe")
def test_get_entity_frequencies(mock_get_articles, mock_session, sample_articles, sample_entities):
    """Test getting entity frequencies."""
    # Setup
    mock_get_articles.return_value = sample_articles
    mock_session.exec.return_value.all.return_value = sample_entities
    
    aggregator = HistoricalDataAggregator(session=mock_session)
    
    # Test with entity types
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    entity_types = ["PERSON", "ORG"]
    
    result = aggregator.get_entity_frequencies(entity_types, start_date)
    
    # Should be executing a query for entities
    mock_session.exec.assert_called()
    
    # Check cache behavior
    cached_result = aggregator.get_entity_frequencies(entity_types, start_date)
    assert cached_result == result
    
    # Clear cache and verify
    aggregator.clear_cache()
    assert aggregator._cache == {}


@patch("local_newsifier.tools.historical_aggregator.HistoricalDataAggregator.get_entity_frequencies")
@patch("local_newsifier.tools.historical_aggregator.HistoricalDataAggregator.calculate_date_range")
def test_get_baseline_frequencies(mock_calculate_date_range, mock_get_entity_frequencies, mock_session):
    """Test getting baseline frequencies for comparison."""
    # Setup
    current_start = datetime.now(timezone.utc) - timedelta(days=7)
    current_end = datetime.now(timezone.utc)
    baseline_start = current_start - timedelta(days=21)  # 3x the current period
    baseline_end = current_start - timedelta(seconds=1)
    
    mock_calculate_date_range.return_value = (current_start, current_end)
    
    current_freqs = {
        "Mayor Johnson:PERSON": TopicFrequency(
            topic="Mayor Johnson", entity_type="PERSON", frequencies={"2023-01-15": 2}, total_mentions=2
        )
    }
    baseline_freqs = {
        "Mayor Johnson:PERSON": TopicFrequency(
            topic="Mayor Johnson", entity_type="PERSON", frequencies={"2023-01-01": 1}, total_mentions=1
        )
    }
    
    mock_get_entity_frequencies.side_effect = [current_freqs, baseline_freqs]
    
    aggregator = HistoricalDataAggregator(session=mock_session)
    
    # Test getting baseline frequencies
    current, baseline = aggregator.get_baseline_frequencies(
        entity_types=["PERSON", "ORG"], time_frame=TimeFrame.WEEK
    )
    
    assert current == current_freqs
    assert baseline == baseline_freqs
    
    # Check that get_entity_frequencies was called with correct date ranges
    assert mock_get_entity_frequencies.call_count == 2