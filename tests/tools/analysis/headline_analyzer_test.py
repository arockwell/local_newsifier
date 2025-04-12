"""Tests for the HeadlineTrendAnalyzer tool."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockFixture

from src.local_newsifier.tools.analysis.headline_analyzer import HeadlineTrendAnalyzer


class TestHeadlineTrendAnalyzer:
    """Tests for the HeadlineTrendAnalyzer class."""

    @pytest.fixture
    def mock_db_manager(self) -> MagicMock:
        """Create a mock database manager."""
        mock = MagicMock()
        mock.session = MagicMock()
        return mock

    @pytest.fixture
    def mock_nlp(self) -> MagicMock:
        """Create a mock NLP model."""
        mock = MagicMock()
        mock.noun_chunks = []
        mock.ents = []
        return mock

    @pytest.fixture
    def analyzer(self, mock_db_manager: MagicMock) -> HeadlineTrendAnalyzer:
        """Create a headline analyzer with mocked components."""
        with patch("spacy.load") as mock_load:
            mock_load.return_value = MagicMock()
            analyzer = HeadlineTrendAnalyzer(mock_db_manager)
            return analyzer

    def test_get_interval_key_day(self, analyzer: HeadlineTrendAnalyzer) -> None:
        """Test getting interval key for day."""
        date = datetime(2023, 5, 15, 12, 30, 0)
        key = analyzer._get_interval_key(date, "day")
        assert key == "2023-05-15"

    def test_get_interval_key_week(self, analyzer: HeadlineTrendAnalyzer) -> None:
        """Test getting interval key for week."""
        date = datetime(2023, 5, 15, 12, 30, 0)
        key = analyzer._get_interval_key(date, "week")
        assert key.startswith("2023-W")

    def test_get_interval_key_month(self, analyzer: HeadlineTrendAnalyzer) -> None:
        """Test getting interval key for month."""
        date = datetime(2023, 5, 15, 12, 30, 0)
        key = analyzer._get_interval_key(date, "month")
        assert key == "2023-05"

    def test_get_headlines_by_period(
        self, analyzer: HeadlineTrendAnalyzer, mock_db_manager: MagicMock
    ) -> None:
        """Test getting headlines grouped by period."""
        # Create sample articles in the database
        start_date = datetime(2023, 5, 1)
        end_date = datetime(2023, 5, 10)
        
        # Mock articles with different dates
        mock_articles = []
        for i in range(10):
            article = MagicMock()
            article.published_at = start_date + timedelta(days=i)
            article.title = f"Test headline {i+1}"
            mock_articles.append(article)
            
        # Set up the mock database query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_order_by.all.return_value = mock_articles
        mock_filter.order_by.return_value = mock_order_by
        mock_query.filter.return_value = mock_filter
        mock_db_manager.session.query.return_value = mock_query
        
        # Call the method
        result = analyzer.get_headlines_by_period(start_date, end_date, "day")
        
        # Verify results
        assert len(result) == 10  # One entry per day
        assert "2023-05-01" in result
        assert result["2023-05-01"][0] == "Test headline 1"

    def test_extract_keywords_with_nlp(self, analyzer: HeadlineTrendAnalyzer) -> None:
        """Test extracting keywords using NLP."""
        headlines = [
            "Local Mayor Announces New Park Development",
            "School Board Approves Budget for Next Year",
            "Mayor Breaks Ground on Park Construction Project"
        ]
        
        # Mock the NLP process
        mock_doc = MagicMock()
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "Local Mayor"
        mock_chunk2 = MagicMock()
        mock_chunk2.text = "New Park Development"
        mock_chunk3 = MagicMock()
        mock_chunk3.text = "School Board"
        mock_chunk4 = MagicMock()
        mock_chunk4.text = "Park Construction Project"
        
        # Set up token checks for is_stop
        token_not_stop = MagicMock()
        token_not_stop.is_stop = False
        
        mock_chunk1.__iter__ = lambda s: iter([token_not_stop])
        mock_chunk2.__iter__ = lambda s: iter([token_not_stop])
        mock_chunk3.__iter__ = lambda s: iter([token_not_stop])
        mock_chunk4.__iter__ = lambda s: iter([token_not_stop])
        
        mock_doc.noun_chunks = [mock_chunk1, mock_chunk2, mock_chunk3, mock_chunk4]
        
        mock_ent1 = MagicMock()
        mock_ent1.text = "Mayor"
        mock_ent1.label_ = "PERSON"
        
        mock_ent2 = MagicMock()
        mock_ent2.text = "School Board"
        mock_ent2.label_ = "ORG"
        
        mock_doc.ents = [mock_ent1, mock_ent2]
        
        analyzer.nlp = MagicMock(return_value=mock_doc)
        
        result = analyzer.extract_keywords(headlines, top_n=5)
        
        # Verify the results contain the expected keywords
        keywords = [kw for kw, count in result]
        assert "local mayor" in keywords or "mayor" in keywords
        assert "school board" in keywords
        assert "park construction project" in keywords or "new park development" in keywords
        
    def test_extract_keywords_without_nlp(self, analyzer: HeadlineTrendAnalyzer) -> None:
        """Test extracting keywords when NLP is not available."""
        headlines = [
            "Local Mayor Announces New Park Development",
            "School Board Approves Budget for Next Year",
            "Mayor Breaks Ground on Park Construction Project"
        ]
        
        # Set NLP to None to trigger fallback behavior
        analyzer.nlp = None
        
        result = analyzer.extract_keywords(headlines, top_n=5)
        
        # Verify simple keyword extraction still works
        assert len(result) > 0
        keywords = [kw for kw, count in result]
        assert any(kw in ["mayor", "park", "school", "board"] for kw in keywords)
        
    def test_extract_keywords_empty_input(self, analyzer: HeadlineTrendAnalyzer) -> None:
        """Test extracting keywords with empty input."""
        result = analyzer.extract_keywords([])
        assert result == []
        
    def test_analyze_trends(
        self, analyzer: HeadlineTrendAnalyzer, mock_db_manager: MagicMock
    ) -> None:
        """Test analyzing trends across time periods."""
        # Mock the get_headlines_by_period and extract_keywords methods
        with patch.object(
            analyzer, 'get_headlines_by_period'
        ) as mock_get_headlines, patch.object(
            analyzer, 'extract_keywords'
        ) as mock_extract_keywords, patch.object(
            analyzer, '_detect_trends'
        ) as mock_detect_trends:
            
            # Set up mock data
            mock_get_headlines.return_value = {
                "2023-05-01": ["Headline 1", "Headline 2"],
                "2023-05-02": ["Headline 3", "Headline 4"]
            }
            
            mock_extract_keywords.side_effect = [
                [("term1", 2), ("term2", 1)],  # for 2023-05-01
                [("term1", 1), ("term3", 2)],  # for 2023-05-02
                [("term1", 3), ("term3", 2), ("term2", 1)]  # for all headlines
            ]
            
            mock_detect_trends.return_value = [
                {"term": "term3", "growth_rate": 2.0, "total_mentions": 2}
            ]
            
            # Call the method
            start_date = datetime(2023, 5, 1)
            end_date = datetime(2023, 5, 2)
            result = analyzer.analyze_trends(start_date, end_date)
            
            # Verify method calls
            mock_get_headlines.assert_called_once_with(start_date, end_date, "day")
            assert mock_extract_keywords.call_count == 3
            mock_detect_trends.assert_called_once()
            
            # Verify results
            assert "trending_terms" in result
            assert "overall_top_terms" in result
            assert "raw_data" in result
            assert "period_counts" in result
            assert result["period_counts"]["2023-05-01"] == 2
            assert result["period_counts"]["2023-05-02"] == 2
            
    def test_detect_trends(self, analyzer: HeadlineTrendAnalyzer) -> None:
        """Test detecting trends from time series data."""
        trend_data = {
            "2023-05-01": [("term1", 1), ("term2", 2)],
            "2023-05-02": [("term1", 2), ("term2", 2)],
            "2023-05-03": [("term1", 4), ("term2", 2)]
        }
        
        result = analyzer._detect_trends(trend_data)
        
        # Verify results
        assert len(result) > 0
        # term1 should be trending (growth from 1 to 4)
        term1_trend = next((t for t in result if t["term"] == "term1"), None)
        assert term1_trend is not None
        assert term1_trend["growth_rate"] > 0
        assert term1_trend["first_count"] == 1
        assert term1_trend["last_count"] == 4
        
        # term2 should not be trending (no growth)
        term2_trend = next((t for t in result if t["term"] == "term2"), None)
        if term2_trend:
            assert term2_trend["growth_rate"] == 0