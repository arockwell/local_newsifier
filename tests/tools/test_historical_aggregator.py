"""Tests for the HistoricalDataAggregator tool."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.local_newsifier.models.database import ArticleDB, EntityDB
from src.local_newsifier.models.trend import TimeFrame, TopicFrequency
from src.local_newsifier.tools.historical_aggregator import HistoricalDataAggregator


@pytest.fixture
def mock_db_manager():
    """Fixture for a mocked DatabaseManager."""
    mock_manager = MagicMock()
    mock_session = MagicMock()
    mock_manager.get_session.return_value.__enter__.return_value = mock_session
    return mock_manager

@pytest.fixture(autouse=True)
def mock_database_config():
    """Fixture to mock database config functions."""
    with patch("src.local_newsifier.tools.historical_aggregator.get_database_settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        yield mock_settings


@pytest.fixture
def sample_articles():
    """Fixture providing sample article data."""
    now = datetime.now(timezone.utc)
    return [
        ArticleDB(
            id=1,
            url="https://example.com/news/article1",
            title="Mayor Johnson announces new development",
            source="Example News",
            published_at=now - timedelta(days=5),
            content="Article content about Mayor Johnson...",
            status="analyzed",
        ),
        ArticleDB(
            id=2,
            url="https://example.com/news/article2",
            title="City Council approves downtown project",
            source="Example News",
            published_at=now - timedelta(days=3),
            content="Article content about City Council...",
            status="analyzed",
        ),
        ArticleDB(
            id=3,
            url="https://example.com/news/article3",
            title="Local businesses react to new development",
            source="Example News",
            published_at=now - timedelta(days=1),
            content="Article content about local businesses...",
            status="analyzed",
        ),
    ]


@pytest.fixture
def sample_entities():
    """Fixture providing sample entity data."""
    return [
        EntityDB(id=1, article_id=1, text="Mayor Johnson", entity_type="PERSON", confidence=0.9),
        EntityDB(id=2, article_id=1, text="City Hall", entity_type="ORG", confidence=0.85),
        EntityDB(id=3, article_id=2, text="City Council", entity_type="ORG", confidence=0.95),
        EntityDB(id=4, article_id=2, text="Downtown Project", entity_type="ORG", confidence=0.9),
        EntityDB(id=5, article_id=3, text="Downtown Project", entity_type="ORG", confidence=0.9),
        EntityDB(id=6, article_id=3, text="Local Businesses", entity_type="ORG", confidence=0.8),
    ]


def test_init():
    """Test HistoricalDataAggregator initialization."""
    with patch("src.local_newsifier.tools.historical_aggregator.DatabaseManager") as mock_db_cls:
        mock_db_instance = MagicMock()
        mock_db_cls.return_value = mock_db_instance
        
        # Test with default initialization
        aggregator = HistoricalDataAggregator()
        assert aggregator.db_manager == mock_db_instance
        assert aggregator._cache == {}
        
        # Test with provided db_manager
        mock_db_manager = MagicMock()
        aggregator = HistoricalDataAggregator(db_manager=mock_db_manager)
        assert aggregator.db_manager == mock_db_manager


def test_get_articles_in_timeframe(mock_db_manager, sample_articles):
    """Test retrieving articles within a timeframe."""
    # Setup
    mock_session = mock_db_manager.get_session.return_value.__enter__.return_value
    mock_session.query.return_value.filter.return_value.filter.return_value.all.return_value = []
    mock_session.query.return_value.filter.return_value.all.return_value = sample_articles
    
    aggregator = HistoricalDataAggregator(db_manager=mock_db_manager)
    
    # Test without source filter
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    end_date = datetime.now(timezone.utc)
    
    result = aggregator.get_articles_in_timeframe(start_date, end_date)
    
    assert result == sample_articles
    mock_session.query.assert_called_with(ArticleDB)
    
    # Test with source filter
    result = aggregator.get_articles_in_timeframe(start_date, end_date, source="Example News")
    
    assert result == []  # Mocked to return empty for source filter
    mock_session.query.assert_called_with(ArticleDB)


def test_calculate_date_range():
    """Test date range calculation for different time frames."""
    aggregator = HistoricalDataAggregator()
    
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


@patch("src.local_newsifier.tools.historical_aggregator.HistoricalDataAggregator.get_articles_in_timeframe")
def test_get_entity_frequencies(mock_get_articles, mock_db_manager, sample_articles, sample_entities):
    """Test getting entity frequencies."""
    # Setup
    mock_get_articles.return_value = sample_articles
    mock_session = mock_db_manager.get_session.return_value.__enter__.return_value
    mock_session.query.return_value.filter.return_value.all.return_value = sample_entities
    
    aggregator = HistoricalDataAggregator(db_manager=mock_db_manager)
    
    # Test with entity types
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    entity_types = ["PERSON", "ORG"]
    
    result = aggregator.get_entity_frequencies(entity_types, start_date)
    
    # Should be fetching entities for all articles
    mock_session.query.assert_called_with(EntityDB)
    
    # Check cache behavior
    cached_result = aggregator.get_entity_frequencies(entity_types, start_date)
    assert cached_result == result
    
    # Clear cache and verify
    aggregator.clear_cache()
    assert aggregator._cache == {}


@patch("src.local_newsifier.tools.historical_aggregator.HistoricalDataAggregator.get_entity_frequencies")
@patch("src.local_newsifier.tools.historical_aggregator.HistoricalDataAggregator.calculate_date_range")
def test_get_baseline_frequencies(mock_calculate_date_range, mock_get_entity_frequencies):
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
    
    aggregator = HistoricalDataAggregator()
    
    # Test getting baseline frequencies
    current, baseline = aggregator.get_baseline_frequencies(
        entity_types=["PERSON", "ORG"], time_frame=TimeFrame.WEEK
    )
    
    assert current == current_freqs
    assert baseline == baseline_freqs
    
    # Check that get_entity_frequencies was called with correct date ranges
    assert mock_get_entity_frequencies.call_count == 2