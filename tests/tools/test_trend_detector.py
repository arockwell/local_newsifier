"""Tests for the TrendDetector tool."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.local_newsifier.models import Article, Entity
# Use legacy imports for testing until fully migrated
from src.local_newsifier.models.database import ArticleDB, EntityDB
from src.local_newsifier.models.trend import (TrendAnalysis, TrendEntity,
                                            TrendEvidenceItem, TrendStatus,
                                            TrendType)
from src.local_newsifier.tools.trend_detector import TrendDetector


@pytest.fixture
def mock_topic_analyzer():
    """Fixture for a mocked TopicFrequencyAnalyzer."""
    return MagicMock()


@pytest.fixture
def mock_data_aggregator():
    """Fixture for a mocked HistoricalDataAggregator."""
    return MagicMock()


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Fixture to mock dependencies."""
    with patch("src.local_newsifier.tools.trend_detector.TopicFrequencyAnalyzer") as mock_analyzer:
        with patch("src.local_newsifier.tools.trend_detector.HistoricalDataAggregator") as mock_agg:
            mock_analyzer.return_value = MagicMock()
            mock_agg.return_value = MagicMock()
            yield mock_analyzer, mock_agg


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


@pytest.fixture
def significance_data():
    """Fixture providing sample significance data."""
    return {
        "topic": "Downtown Project",
        "entity_type": "ORG",
        "current_frequency": 5,
        "baseline_frequency": 2,
        "change_percent": 150.0,
        "z_score": 2.5,
        "is_new": False,
        "lookback_days": timedelta(days=7),
    }


@pytest.fixture
def pattern_data():
    """Fixture providing sample pattern data."""
    return {
        "topic": "Downtown Project",
        "entity_type": "ORG",
        "total_mentions": 6,
        "peak_date": "2023-01-03",
        "peak_value": 3,
        "slope": 0.8,
        "is_rising": True,
        "is_falling": False,
        "is_spiky": False,
        "is_consistent": False,
        "coefficient_of_variation": 0.6,
    }


@pytest.fixture
def related_topics():
    """Fixture providing sample related topics data."""
    return [
        {
            "topic": "City Council",
            "entity_type": "ORG",
            "co_occurrence_rate": 0.67,
            "co_occurrence_count": 2,
        },
        {
            "topic": "Local Businesses",
            "entity_type": "ORG",
            "co_occurrence_rate": 0.33,
            "co_occurrence_count": 1,
        },
    ]


def test_init(mock_topic_analyzer, mock_data_aggregator):
    """Test TrendDetector initialization."""
    with patch("src.local_newsifier.tools.trend_detector.TopicFrequencyAnalyzer") as mock_analyzer_cls:
        with patch("src.local_newsifier.tools.trend_detector.HistoricalDataAggregator") as mock_agg_cls:
            mock_analyzer_instance = MagicMock()
            mock_agg_instance = MagicMock()
            mock_analyzer_cls.return_value = mock_analyzer_instance
            mock_agg_cls.return_value = mock_agg_instance
            
            # Test with default initialization
            detector = TrendDetector()
            assert detector.data_aggregator == mock_agg_instance
            assert detector.topic_analyzer == mock_analyzer_instance
            
            # Test with provided components
            detector = TrendDetector(
                topic_analyzer=mock_topic_analyzer,
                data_aggregator=mock_data_aggregator,
            )
            assert detector.data_aggregator == mock_data_aggregator
            assert detector.topic_analyzer == mock_topic_analyzer


@patch("src.local_newsifier.tools.trend_detector.TrendDetector._get_articles_for_entity")
def test_create_trend_from_topic(
    mock_get_articles, mock_topic_analyzer, mock_data_aggregator, 
    significance_data, pattern_data, related_topics
):
    """Test creation of trend from topic data."""
    detector = TrendDetector(
        topic_analyzer=mock_topic_analyzer,
        data_aggregator=mock_data_aggregator,
    )
    
    # Test creating an EMERGING_TOPIC trend
    trend = detector._create_trend_from_topic(
        "Downtown Project", "ORG", significance_data, pattern_data, related_topics
    )
    
    assert isinstance(trend, TrendAnalysis)
    assert trend.trend_type == TrendType.EMERGING_TOPIC
    assert trend.name == "Downtown Project (ORG)"
    assert "increasing coverage" in trend.description.lower()
    assert trend.confidence_score > 0.6
    assert trend.start_date is not None
    assert trend.statistical_significance == significance_data["z_score"]
    assert len(trend.entities) == 1 + len(related_topics)  # Main entity + related
    assert trend.entities[0].text == "Downtown Project"
    assert trend.entities[0].entity_type == "ORG"
    
    # Test creating a NOVEL_ENTITY trend
    significance_data["is_new"] = True
    trend = detector._create_trend_from_topic(
        "New Entity", "PERSON", significance_data, None, []
    )
    
    assert trend.trend_type == TrendType.NOVEL_ENTITY
    assert "new person" in trend.description.lower()
    
    # Test creating a SUSTAINED_COVERAGE trend
    significance_data["is_new"] = False
    pattern_data["is_rising"] = False
    pattern_data["is_consistent"] = True
    trend = detector._create_trend_from_topic(
        "Consistent Topic", "GPE", significance_data, pattern_data, []
    )
    
    assert trend.trend_type == TrendType.SUSTAINED_COVERAGE
    assert "consistent" in trend.description.lower()
    
    # Test creating a FREQUENCY_SPIKE trend
    pattern_data["is_consistent"] = False
    trend = detector._create_trend_from_topic(
        "Spike Topic", "ORG", significance_data, pattern_data, []
    )
    
    assert trend.trend_type == TrendType.FREQUENCY_SPIKE
    assert "increase" in trend.description.lower()


@patch("src.local_newsifier.tools.trend_detector.TrendDetector._get_articles_for_entity")
@patch("src.local_newsifier.tools.trend_detector.TrendDetector._create_trend_from_topic")
@patch("src.local_newsifier.tools.trend_detector.TrendDetector._add_evidence_to_trend")
def test_detect_entity_trends(
    mock_add_evidence, mock_create_trend, mock_get_articles,
    mock_topic_analyzer, mock_data_aggregator, sample_articles
):
    """Test detection of entity trends."""
    # Setup mocks
    mock_topic_analyzer.identify_significant_changes.return_value = {
        "Downtown Project:ORG": {"topic": "Downtown Project", "entity_type": "ORG"},
        "Mayor Johnson:PERSON": {"topic": "Mayor Johnson", "entity_type": "PERSON"},
    }
    
    mock_data_aggregator.get_baseline_frequencies.return_value = ({}, {})
    mock_topic_analyzer.analyze_frequency_patterns.return_value = {}
    mock_topic_analyzer.find_related_topics.return_value = []
    mock_data_aggregator.calculate_date_range.return_value = (
        datetime.now(timezone.utc) - timedelta(days=7),
        datetime.now(timezone.utc),
    )
    
    mock_get_articles.return_value = sample_articles
    
    # Setup trend objects for the mock
    trend1 = TrendAnalysis(
        trend_type=TrendType.EMERGING_TOPIC,
        name="Downtown Project (ORG)",
        description="Test description",
        confidence_score=0.9,
        start_date=datetime.now(timezone.utc),
    )
    
    trend2 = TrendAnalysis(
        trend_type=TrendType.FREQUENCY_SPIKE,
        name="Mayor Johnson (PERSON)",
        description="Test description",
        confidence_score=0.8,
        start_date=datetime.now(timezone.utc),
    )
    
    # Set return values for create_trend_from_topic
    mock_create_trend.side_effect = [trend1, trend2]
    
    # Set return values for add_evidence_to_trend
    mock_add_evidence.side_effect = lambda trend, articles: trend
    
    detector = TrendDetector(
        topic_analyzer=mock_topic_analyzer,
        data_aggregator=mock_data_aggregator,
    )
    
    # Test trend detection
    trends = detector.detect_entity_trends(
        entity_types=["PERSON", "ORG", "GPE"],
        min_significance=1.5,
        min_mentions=2,
    )
    
    assert len(trends) == 2
    assert trends[0].name == "Downtown Project (ORG)"
    assert trends[1].name == "Mayor Johnson (PERSON)"
    
    # Check that the appropriate methods were called
    mock_topic_analyzer.identify_significant_changes.assert_called_once()
    mock_data_aggregator.get_baseline_frequencies.assert_called_once()
    mock_topic_analyzer.analyze_frequency_patterns.assert_called_once()
    assert mock_topic_analyzer.find_related_topics.call_count == 2
    assert mock_get_articles.call_count == 2
    assert mock_create_trend.call_count == 2
    assert mock_add_evidence.call_count == 2


def test_get_articles_for_entity(
    mock_topic_analyzer, mock_data_aggregator, sample_articles, sample_entities
):
    """Test retrieving articles for a specific entity."""
    # Setup
    mock_data_aggregator.get_articles_in_timeframe.return_value = sample_articles
    
    # Create article lookup dict
    article_lookup = {article.id: article for article in sample_articles}
    
    # Filter entities for "Downtown Project"
    downtown_entities = [e for e in sample_entities if e.text == "Downtown Project"]
    
    # Mock session query
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.all.return_value = downtown_entities
    mock_data_aggregator.db_manager.get_session.return_value.__enter__.return_value = mock_session
    
    detector = TrendDetector(
        topic_analyzer=mock_topic_analyzer,
        data_aggregator=mock_data_aggregator,
    )
    
    # Test getting articles for "Downtown Project"
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    end_date = datetime.now(timezone.utc)
    
    result = detector._get_articles_for_entity(
        "Downtown Project", "ORG", start_date, end_date
    )
    
    # Check that the right methods were called
    mock_data_aggregator.get_articles_in_timeframe.assert_called_with(start_date, end_date)
    
    # Since we changed the code to use SQLModel select() instead of query(),
    # we no longer need to check for query calls
    # mock_session.query.assert_called_with(EntityDB)
    
    # Test with no articles
    mock_data_aggregator.get_articles_in_timeframe.return_value = []
    result = detector._get_articles_for_entity(
        "Downtown Project", "ORG", start_date, end_date
    )
    assert result == []


def test_add_evidence_to_trend(sample_articles):
    """Test adding evidence to a trend from articles."""
    detector = TrendDetector()
    
    # Create a trend
    trend = TrendAnalysis(
        trend_type=TrendType.EMERGING_TOPIC,
        name="Downtown Project (ORG)",
        description="Test description",
        confidence_score=0.9,
        start_date=datetime.now(timezone.utc),
    )
    
    # Test adding evidence - sort articles by date, newest first
    sorted_articles = sorted(sample_articles, key=lambda a: a.published_at, reverse=True)
    result = detector._add_evidence_to_trend(trend, sample_articles)
    
    assert len(result.evidence) == len(sample_articles)
    for i, evidence in enumerate(result.evidence):
        assert evidence.article_url == sorted_articles[i].url
        assert evidence.article_title == sorted_articles[i].title
        assert evidence.published_at == sorted_articles[i].published_at
        
    # Create a fresh trend for testing limit
    fresh_trend = TrendAnalysis(
        trend_type=TrendType.EMERGING_TOPIC,
        name="Downtown Project (ORG)",
        description="Test description",
        confidence_score=0.9,
        start_date=datetime.now(timezone.utc),
    )
    
    # Test with more than 10 articles (should limit to 10)
    many_articles = sample_articles * 4  # 12 articles
    result = detector._add_evidence_to_trend(fresh_trend, many_articles)
    
    # Should have exactly 10 evidence items
    assert len(result.evidence) == 10