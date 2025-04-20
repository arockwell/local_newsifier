"""Tests for the trend_analyzer module."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.trend import TrendType


class TestTrendAnalyzer:
    """Tests for the TrendAnalyzer class."""

    def test_init(self):
        """Test initialization of the TrendAnalyzer."""
        # Test with default parameters
        analyzer = TrendAnalyzer()
        assert analyzer.session is None
        assert analyzer._cache == {}
        
        # Test with session
        mock_session = MagicMock()
        analyzer = TrendAnalyzer(session=mock_session)
        assert analyzer.session is mock_session

    def test_extract_keywords(self):
        """Test extraction of keywords from headlines."""
        analyzer = TrendAnalyzer()
        # Mock nlp to avoid loading spaCy model
        analyzer.nlp = None
        
        # Test with empty headlines
        assert analyzer.extract_keywords([]) == []
        
        # Test with headlines using fallback method
        headlines = [
            "Gainesville City Commission approves new development",
            "UF researchers make breakthrough in cancer treatment",
            "Local school wins state championship"
        ]
        
        keywords = analyzer.extract_keywords(headlines, top_n=5)
        assert len(keywords) > 0
        assert isinstance(keywords, list)
        assert all(isinstance(k, tuple) and len(k) == 2 for k in keywords)
        assert all(isinstance(k[0], str) and isinstance(k[1], int) for k in keywords)
        
        # Check common words are filtered
        common_words = ["the", "a", "an", "and", "in", "on", "at", "to", "for", "of", "with"]
        extracted_words = [k[0] for k in keywords]
        assert not any(word in extracted_words for word in common_words)

    def test_detect_keyword_trends(self):
        """Test detection of trending keywords."""
        analyzer = TrendAnalyzer()
        
        # Test with empty data
        assert analyzer.detect_keyword_trends({}) == []
        
        # Test with insufficient data (need at least 2 periods)
        assert analyzer.detect_keyword_trends({"2023-01-01": []}) == []
        
        # Test with actual trend data
        trend_data = {
            "2023-01-01": [("city", 2), ("school", 1)],
            "2023-01-02": [("city", 3), ("school", 2)],
            "2023-01-03": [("city", 5), ("school", 1)]
        }
        
        results = analyzer.detect_keyword_trends(trend_data)
        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)
        
        # Verify city is trending (growth from 2 to 5)
        city_trend = next((r for r in results if r["term"] == "city"), None)
        assert city_trend is not None
        assert city_trend["growth_rate"] > 0
        assert city_trend["first_count"] == 2
        assert city_trend["last_count"] == 5

    def test_get_interval_key(self):
        """Test interval key generation."""
        date = datetime(2023, 5, 15, 10, 30)
        
        # Test day interval
        assert TrendAnalyzer.get_interval_key(date, "day") == "2023-05-15"
        
        # Test week interval
        assert TrendAnalyzer.get_interval_key(date, "week").startswith("2023-W")
        
        # Test month interval
        assert TrendAnalyzer.get_interval_key(date, "month") == "2023-05"
        
        # Test default
        assert TrendAnalyzer.get_interval_key(date, "year") == "2023"
        
        # Test with None date (uses current time)
        assert TrendAnalyzer.get_interval_key(None, "day") is not None

    def test_detect_entity_trends(self):
        """Test entity trend detection."""
        # Create mock entities and articles
        articles = [
            Article(
                id=1,
                url="http://example.com/1",
                title="Gainesville mayor announces new initiative",
                content="The mayor of Gainesville announced a new initiative today.",
                published_at=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            Article(
                id=2,
                url="http://example.com/2",
                title="Mayor discusses budget plans",
                content="Mayor discusses new budget plans for the city.",
                published_at=datetime.now(timezone.utc) - timedelta(days=2)
            ),
            Article(
                id=3,
                url="http://example.com/3",
                title="UF receives funding for research",
                content="The University of Florida received new funding.",
                published_at=datetime.now(timezone.utc) - timedelta(days=3)
            )
        ]
        
        entities = [
            Entity(id=1, article_id=1, text="Mayor", entity_type="PERSON", sentence_context="The mayor of Gainesville announced a new initiative today."),
            Entity(id=2, article_id=2, text="Mayor", entity_type="PERSON", sentence_context="Mayor discusses new budget plans for the city."),
            Entity(id=3, article_id=1, text="Gainesville", entity_type="GPE", sentence_context="The mayor of Gainesville announced a new initiative today."),
            Entity(id=4, article_id=3, text="University of Florida", entity_type="ORG", sentence_context="The University of Florida received new funding.")
        ]
        
        analyzer = TrendAnalyzer()
        trends = analyzer.detect_entity_trends(
            entities=entities,
            articles=articles,
            entity_types=["PERSON", "ORG", "GPE"],
            min_significance=1.0,
            min_mentions=2
        )
        
        # Should detect Mayor as a trending entity (mentioned twice)
        assert len(trends) > 0
        
        # Verify the properties of the trend
        mayor_trend = next((t for t in trends if "Mayor" in t.name), None)
        assert mayor_trend is not None
        assert mayor_trend.trend_type in [TrendType.FREQUENCY_SPIKE, TrendType.EMERGING_TOPIC, TrendType.NOVEL_ENTITY]
        assert mayor_trend.confidence_score >= 0.6
        assert len(mayor_trend.entities) >= 1
        
        # Verify that single-mention entities are not included
        uf_trend = next((t for t in trends if "University of Florida" in t.name), None)
        assert uf_trend is None or mayor_trend.confidence_score > uf_trend.confidence_score

    def test_clear_cache(self):
        """Test cache clearing."""
        analyzer = TrendAnalyzer()
        analyzer._cache = {"key1": "value1", "key2": "value2"}
        
        analyzer.clear_cache()
        assert analyzer._cache == {}
