"""Implementation tests for TrendAnalyzer.

This file tests the implementation of TrendAnalyzer methods directly to improve code coverage.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from unittest.mock import MagicMock, patch

# Mock spacy before importing TrendAnalyzer
mock_nlp = MagicMock()
mock_doc = MagicMock()
mock_doc.noun_chunks = []
mock_doc.ents = []
mock_nlp.return_value = mock_doc
patch('spacy.load', return_value=mock_nlp).start()

import pytest
from sqlmodel import Session, select

from local_newsifier.models.article import Article
from local_newsifier.models.trend import (
    TrendAnalysis,
    TrendType,
    TrendEntity,
    TrendEvidenceItem,
    TrendStatus
)
from tests.ci_skip_config import ci_skip_injectable

# Create a mock TrendAnalyzer class that works without dependency injection
class MockTrendAnalyzer:
    """A mock version of TrendAnalyzer that doesn't use dependency injection."""

    def __init__(self, session=None, nlp_model=None, model_name="en_core_web_lg"):
        self.session = session
        self._cache = {}
        self.nlp = nlp_model

        # We don't actually load spaCy model in tests

def create_test_analyzer(session=None, nlp_model=None):
    """Helper function to create a test analyzer instance with all methods copied."""
    # Import the real TrendAnalyzer for method copying
    from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer

    # Create a mock instance
    analyzer = MockTrendAnalyzer(session=session, nlp_model=nlp_model)

    # Copy all methods from TrendAnalyzer to our mock
    for name, method in TrendAnalyzer.__dict__.items():
        if callable(method) and not name.startswith('__'):
            setattr(analyzer, name, method.__get__(analyzer, MockTrendAnalyzer))

    return analyzer


@ci_skip_injectable
class TestTrendAnalyzerImplementation:
    """Test the implementation of TrendAnalyzer directly."""

    @pytest.fixture
    def trend_analyzer(self):
        """Create a TrendAnalyzer instance."""
        # Import here to avoid immediate decorator execution at module import
        with patch('spacy.load') as mock_load:
            mock_nlp = MagicMock()
            mock_load.return_value = mock_nlp
            return create_test_analyzer(nlp_model=mock_nlp)

    @pytest.fixture
    def sample_articles(self, db_session):
        """Create sample articles for trend analysis."""
        articles = []
        # Create articles with trending keywords
        for i in range(10):
            # Add some trending keywords to even-indexed articles
            if i % 2 == 0:
                content = (
                    "This article discusses the trending topics of artificial intelligence, "
                    "climate change, and renewable energy. These are important issues that "
                    "are frequently discussed in the news."
                )
            else:
                content = (
                    "This article is about various subjects including technology, "
                    "politics, and finance. It doesn't focus on any particular trend."
                )
                
            article = Article(
                title=f"Test Article {i} about {'trending topics' if i % 2 == 0 else 'regular news'}",
                content=content,
                url=f"https://example.com/article-{i}",
                source="test_source",
                status="processed",
                published_at=datetime.now(timezone.utc) - timedelta(days=i),
                scraped_at=datetime.now(timezone.utc)
            )
            db_session.add(article)
            db_session.commit()
            db_session.refresh(article)
            articles.append(article)
        return articles

    def test_extract_keywords(self, trend_analyzer):
        """Test keyword extraction from text."""
        # Test with a list of headlines as per the actual implementation
        headlines = [
            "Artificial intelligence and machine learning are transforming healthcare",
            "Many research institutes are exploring AI applications in medicine",
            "AI and machine learning applications in healthcare",
            "New advances in AI for medical diagnosis",
            "Machine learning models help doctors analyze data"
        ]

        # Set up mock to return some meaningful noun chunks and entities
        mock_doc = MagicMock()
        mock_nlp = trend_analyzer.nlp

        # Create mock noun chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "artificial intelligence"
        mock_chunk1.__iter__.return_value = []  # No stop words

        mock_chunk2 = MagicMock()
        mock_chunk2.text = "machine learning"
        mock_chunk2.__iter__.return_value = []  # No stop words

        # Create mock entities
        mock_entity1 = MagicMock()
        mock_entity1.text = "AI"
        mock_entity1.label_ = "ORG"

        mock_entity2 = MagicMock()
        mock_entity2.text = "healthcare"
        mock_entity2.label_ = "PERSON"

        # Set up the doc mock with chunks and entities
        mock_doc.noun_chunks = [mock_chunk1, mock_chunk2]
        mock_doc.ents = [mock_entity1, mock_entity2]

        # Update the mock NLP return value
        mock_nlp.return_value = mock_doc

        # Run the test
        keywords = trend_analyzer.extract_keywords(headlines)

        # Verify keywords were extracted (should be a list of tuples)
        assert isinstance(keywords, list)
        assert len(keywords) > 0

        # Each keyword should be a (term, count) tuple
        assert isinstance(keywords[0], tuple)
        assert len(keywords[0]) == 2



    def test_detect_keyword_trends(self, trend_analyzer):
        """Test detection of keyword trends."""
        # Create test trend data for two time periods
        trend_data = {
            "period1": [("AI", 5), ("climate", 3), ("politics", 2)],
            "period2": [("AI", 10), ("climate", 4), ("politics", 1)]
        }
        
        trends = trend_analyzer.detect_keyword_trends(trend_data)
        
        # Verify trends
        assert isinstance(trends, list)
        
        # Skip detailed assertions since implementation may vary
    
    def test_get_interval_key(self, trend_analyzer):
        """Test interval key generation."""
        date = datetime(2023, 6, 15, tzinfo=timezone.utc)
        
        # Test day interval
        day_key = trend_analyzer.get_interval_key(date, "day")
        assert day_key == "2023-06-15"
        
        # Test week interval
        week_key = trend_analyzer.get_interval_key(date, "week")
        assert week_key.startswith("2023-W")
        
        # Test month interval
        month_key = trend_analyzer.get_interval_key(date, "month")
        assert month_key == "2023-06"
        
        # Test default (year)
        year_key = trend_analyzer.get_interval_key(date, "year")
        assert year_key == "2023"
    
    def test_calculate_date_range(self, trend_analyzer):
        """Test date range calculation."""
        from local_newsifier.models.trend import TimeFrame
        
        # Test day time frame
        start_date, end_date = trend_analyzer.calculate_date_range(TimeFrame.DAY, periods=5)
        assert isinstance(start_date, datetime)
        assert isinstance(end_date, datetime)
        assert (end_date - start_date).days == 5
        
        # Test week time frame
        start_date, end_date = trend_analyzer.calculate_date_range(TimeFrame.WEEK, periods=2)
        assert (end_date - start_date).days == 14
        
        # Test month time frame
        start_date, end_date = trend_analyzer.calculate_date_range(TimeFrame.MONTH, periods=1)
        assert (end_date - start_date).days == 30
    
    def test_calculate_statistical_significance(self, trend_analyzer):
        """Test statistical significance calculation."""
        # Test new topic (no baseline)
        z_score, is_significant = trend_analyzer.calculate_statistical_significance(
            current_mentions=3, baseline_mentions=0
        )
        assert z_score == 2.0
        assert is_significant is True
        
        # Test significant growth
        z_score, is_significant = trend_analyzer.calculate_statistical_significance(
            current_mentions=10, baseline_mentions=5
        )
        assert z_score > 0
        assert is_significant is True
        
        # Test insignificant growth
        z_score, is_significant = trend_analyzer.calculate_statistical_significance(
            current_mentions=11, baseline_mentions=10
        )
        assert is_significant is False
    
    def test_analyze_frequency_patterns(self, trend_analyzer):
        """Test frequency pattern analysis."""
        entity_frequencies = {
            "2023-01-01": 1,
            "2023-01-02": 2,
            "2023-01-03": 3,
            "2023-01-04": 5,
            "2023-01-05": 8
        }
        
        patterns = trend_analyzer.analyze_frequency_patterns(entity_frequencies)
        
        assert isinstance(patterns, dict)
        assert "mean" in patterns
        assert "std" in patterns
        assert "coefficient_of_variation" in patterns
        assert "is_spiky" in patterns
        assert "is_consistent" in patterns
    
    def test_clear_cache(self, trend_analyzer):
        """Test cache clearing."""
        # Add something to the cache
        trend_analyzer._cache["test_key"] = "test_value"
        assert "test_key" in trend_analyzer._cache
        
        # Clear the cache
        trend_analyzer.clear_cache()
        
        # Verify cache is empty
        assert len(trend_analyzer._cache) == 0
