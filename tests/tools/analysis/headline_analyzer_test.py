"""Tests for the HeadlineTrendAnalyzer tool."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockFixture
import logging
from sqlmodel import Session

from local_newsifier.tools.analysis.headline_analyzer import HeadlineTrendAnalyzer
from local_newsifier.models.article import Article

logger = logging.getLogger(__name__)

# Replace actual spaCy loading with mock for this module
@pytest.fixture(autouse=True)
def mock_spacy_load(monkeypatch):
    """Mock spaCy.load for all tests in this module."""
    def mock_load(model_name):
        # Return a mock model
        mock_model = MagicMock()
        # Configure the mock to handle the __call__ method
        mock_model.side_effect = lambda text: MagicMock(
            noun_chunks=[],
            ents=[]
        )
        return mock_model
    
    monkeypatch.setattr("spacy.load", mock_load)

@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a test database session."""
    with Session(test_engine) as session:
        yield session

@pytest.fixture
def mock_nlp():
    """Create a mock spaCy model."""
    def create_mock_doc(text):
        mock_doc = MagicMock()
        
        # Handle trending topic test case
        trending_count = text.count("Trending Topic Test")
        if trending_count > 0:
            mock_doc.noun_chunks = [MagicMock(text="Trending Topic Test", tokens=[MagicMock(is_stop=False)])] * trending_count
            mock_doc.ents = [MagicMock(text="Trending Topic Test", label_="ORG")] * trending_count
            return mock_doc
            
        # Handle basic test case
        test_count = text.count("Test Article")
        if test_count > 0:
            mock_doc.noun_chunks = [MagicMock(text="Test Article", tokens=[MagicMock(is_stop=False)])] * test_count
            mock_doc.ents = [MagicMock(text="Test", label_="ORG")] * test_count
            return mock_doc
            
        # Default case
        mock_doc.noun_chunks = []
        mock_doc.ents = []
        return mock_doc
    
    mock_nlp = MagicMock()
    mock_nlp.side_effect = create_mock_doc
    return mock_nlp

def test_headline_analyzer_with_real_db(test_session, mock_nlp):
    """Test headline analyzer with real database session."""
    with patch("spacy.load", return_value=mock_nlp):
        # Create test articles
        now = datetime.now()
        articles = [
            Article(
                url=f"https://example.com/article{i}",
                title=f"Test Article {i}",
                content=f"Content {i}",
                published_at=now,
                status="analyzed",
                source="test_source",
                scraped_at=now  # Added scraped_at field
            )
            for i in range(5)
        ]
        
        # Add articles to database
        for article in articles:
            test_session.add(article)
        test_session.commit()
        
        # Create analyzer with real database session
        analyzer = HeadlineTrendAnalyzer(session=test_session)
        
        # Test getting headlines - explicitly pass the session
        start_date = now - timedelta(days=1)
        end_date = now + timedelta(days=1)
        headlines = analyzer.get_headlines_by_period(start_date, end_date, "day", session=test_session)
        
        # Verify results
        assert len(headlines) > 0
        assert any("Test Article" in headline for headlines_list in headlines.values() for headline in headlines_list)
        
        # Test keyword extraction
        all_headlines = [headline for headlines_list in headlines.values() for headline in headlines_list]
        keywords = analyzer.extract_keywords(all_headlines)
        assert len(keywords) > 0
        assert any("test" in kw.lower() for kw, _ in keywords)
        
        # Test trend analysis - explicitly pass the session
        trends = analyzer.analyze_trends(start_date, end_date, session=test_session)
        assert "trending_terms" in trends
        assert "overall_top_terms" in trends
        assert "raw_data" in trends
        assert "period_counts" in trends

def test_headline_analyzer_with_real_db_and_trends(test_session, mock_nlp, caplog):
    """Test headline analyzer with real database and trending terms."""
    caplog.set_level(logging.DEBUG)
    with patch("spacy.load", return_value=mock_nlp):
        # Create test articles with increasing frequency of a term
        now = datetime.now()
        articles = []
        
        # Create articles with a clear trend
        for i in range(3):  # Reduce the number of days to make trend more clear
            # Add more articles each day
            num_articles = i + 1  # 1 on day 1, 2 on day 2, 3 on day 3
            for j in range(num_articles):
                articles.append(
                    Article(
                        url=f"https://example.com/article{i}_{j}",
                        title=f"Trending Topic Test",  # Use exact same term to ensure trend
                        content=f"Content {i}_{j}",
                        published_at=now - timedelta(days=2-i),  # Most recent first
                        status="analyzed",
                        source="test_source",
                        scraped_at=now  # Added scraped_at field
                    )
                )
        
        # Add articles to database
        for article in articles:
            test_session.add(article)
        test_session.commit()
        
        # Create analyzer with real database session
        analyzer = HeadlineTrendAnalyzer(session=test_session)
        
        # Test trend analysis - explicitly pass the session
        start_date = now - timedelta(days=3)
        end_date = now
        trends = analyzer.analyze_trends(start_date, end_date, time_interval="day", session=test_session)
        
        # Log the results for debugging
        logger.debug("Trend analysis results: %s", trends)
        
        # Verify trending terms
        assert "trending_terms" in trends
        trending_terms = trends["trending_terms"]
        assert len(trending_terms) > 0, f"No trending terms found. Raw data: {trends['raw_data']}"
        
        # Find the trending topic
        trending_topic = next((term for term in trending_terms if "trending" in term["term"].lower()), None)
        assert trending_topic is not None, f"Expected 'trending' in trending terms, got {trending_terms}"
        assert trending_topic["growth_rate"] > 0
        assert trending_topic["total_mentions"] >= 3

def test_headline_analyzer_with_real_db_and_noise(test_session, mock_nlp):
    """Test headline analyzer with real database and noise filtering."""
    with patch("spacy.load", return_value=mock_nlp):
        # Create test articles with some noisy terms
        now = datetime.now()
        articles = []
        
        # Add some articles with noisy terms (appearing only once or twice)
        for i in range(2):
            articles.append(
                Article(
                    url=f"https://example.com/noise{i}",
                    title=f"Noisy Term {i}",
                    content=f"Content {i}",
                    published_at=now - timedelta(days=i),
                    status="analyzed",
                    source="test_source",
                    scraped_at=now  # Added scraped_at field
                )
            )
        
        # Add articles to database
        for article in articles:
            test_session.add(article)
        test_session.commit()
        
        # Create analyzer with real database session
        analyzer = HeadlineTrendAnalyzer(session=test_session)
        
        # Test trend analysis - explicitly pass the session
        start_date = now - timedelta(days=10)
        end_date = now
        trends = analyzer.analyze_trends(start_date, end_date, time_interval="day", session=test_session)
        
        # Verify noisy terms are filtered out
        assert "trending_terms" in trends
        trending_terms = trends["trending_terms"]
        noisy_terms = [term for term in trending_terms if "noisy" in term["term"].lower()]
        assert len(noisy_terms) == 0

class TestHeadlineTrendAnalyzer:
    """Tests for the HeadlineTrendAnalyzer class."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_nlp(self) -> MagicMock:
        """Create a mock NLP model."""
        mock = MagicMock()
        mock.noun_chunks = []
        mock.ents = []
        return mock

    @pytest.fixture
    def analyzer(self, mock_session: MagicMock) -> HeadlineTrendAnalyzer:
        """Create a headline analyzer with mocked components."""
        with patch("spacy.load") as mock_load:
            mock_load.return_value = MagicMock()
            analyzer = HeadlineTrendAnalyzer(session=mock_session)
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
        self, analyzer: HeadlineTrendAnalyzer, mock_session: MagicMock
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
            
        # Set up the mock database query for SQLModel
        mock_session.exec.return_value.all.return_value = mock_articles
        
        # Call the method with mock_session
        result = analyzer.get_headlines_by_period(start_date, end_date, "day", session=mock_session)
        
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
        self, analyzer: HeadlineTrendAnalyzer, mock_session: MagicMock
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
            
            # Call the method with mock_session
            start_date = datetime(2023, 5, 1)
            end_date = datetime(2023, 5, 2)
            result = analyzer.analyze_trends(start_date, end_date, session=mock_session)
            
            # Verify method calls
            mock_get_headlines.assert_called_once_with(start_date, end_date, "day", session=mock_session)
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

    def test_init_with_invalid_nlp_model(self, mock_session: MagicMock) -> None:
        """Test initialization with an invalid spaCy model."""
        with patch("spacy.load") as mock_load:
            mock_load.side_effect = OSError("Model not found")
            analyzer = HeadlineTrendAnalyzer(session=mock_session, nlp_model="invalid_model")
            assert analyzer.nlp is None

    def test_get_headlines_by_period_with_empty_title(
        self, analyzer: HeadlineTrendAnalyzer, mock_session: MagicMock
    ) -> None:
        """Test handling of articles with empty titles."""
        # Create sample articles with empty title
        mock_article = MagicMock()
        mock_article.title = None
        mock_article.published_at = datetime(2023, 5, 1)
        
        # Set up mock database query
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_order_by = MagicMock()
        mock_order_by.all.return_value = [mock_article]
        mock_filter.order_by.return_value = mock_order_by
        mock_query.filter.return_value = mock_filter
        mock_session.query.return_value = mock_query
        
        # Call the method
        result = analyzer.get_headlines_by_period(
            datetime(2023, 5, 1),
            datetime(2023, 5, 2),
            "day"
        )
        
        # Verify empty title was skipped
        assert result == {}

    def test_analyze_trends_no_headlines(
        self, analyzer: HeadlineTrendAnalyzer, mock_session: MagicMock
    ) -> None:
        """Test handling when no headlines are found in the period."""
        with patch.object(analyzer, 'get_headlines_by_period') as mock_get_headlines:
            mock_get_headlines.return_value = {}
            
            result = analyzer.analyze_trends(
                datetime(2023, 5, 1),
                datetime(2023, 5, 2)
            )
            
            assert result == {"error": "No headlines found in the specified period"}

    def test_detect_trends_noise_filtering(
        self, analyzer: HeadlineTrendAnalyzer
    ) -> None:
        """Test filtering of low-frequency terms."""
        trend_data = {
            "2023-05-01": [("term1", 1), ("term2", 1)],
            "2023-05-02": [("term1", 1), ("term2", 1)],
            "2023-05-03": [("term1", 1)]  # term2 disappears
        }
        
        result = analyzer._detect_trends(trend_data)
        
        # Verify low-frequency terms are filtered out
        assert len(result) == 0

    def test_detect_trends_growth_calculation(
        self, analyzer: HeadlineTrendAnalyzer
    ) -> None:
        """Test growth rate calculation for trending terms."""
        trend_data = {
            "2023-05-01": [("term1", 2), ("term2", 1)],
            "2023-05-02": [("term1", 3), ("term2", 1)],
            "2023-05-03": [("term1", 6), ("term2", 1)]  # term1 triples
        }
        
        result = analyzer._detect_trends(trend_data)
        
        # Verify growth rate calculation
        term1_trend = next((t for t in result if t["term"] == "term1"), None)
        assert term1_trend is not None
        assert term1_trend["growth_rate"] == 2.0  # (6-2)/2
        assert term1_trend["first_count"] == 2
        assert term1_trend["last_count"] == 6
        assert term1_trend["total_mentions"] == 11

    def test_get_interval_key_default_year(
        self, analyzer: HeadlineTrendAnalyzer
    ) -> None:
        """Test default year format when interval is invalid."""
        date = datetime(2023, 5, 15)
        key = analyzer._get_interval_key(date, "invalid_interval")
        assert key == "2023"

    def test_detect_trends_term_frequency_threshold(
        self, analyzer: HeadlineTrendAnalyzer
    ) -> None:
        """Test filtering terms based on total frequency threshold and growth rate."""
        # Test case 1: Term appears less than 3 times total but in both first and last period
        trend_data = {
            "2023-05-01": [("term1", 1)],
            "2023-05-02": [("term1", 0)],
            "2023-05-03": [("term1", 1)]  # term1 appears in first and last period
        }
        
        result = analyzer._detect_trends(trend_data)
        
        # Verify term is filtered out due to low total frequency
        assert len(result) == 0
        
        # Test case 2: Term appears 3 times but doesn't have significant growth
        trend_data = {
            "2023-05-01": [("term2", 1)],
            "2023-05-02": [("term2", 1)],
            "2023-05-03": [("term2", 1)]  # term2 appears 3 times but no growth
        }
        
        result = analyzer._detect_trends(trend_data)
        
        # Verify term is filtered out due to no significant growth
        assert len(result) == 0
        
        # Test case 3: Term appears 3 times with significant growth
        trend_data = {
            "2023-05-01": [("term3", 1)],
            "2023-05-02": [("term3", 2)],
            "2023-05-03": [("term3", 3)]  # term3 shows growth and appears 6 times total
        }
        
        result = analyzer._detect_trends(trend_data)
        
        # Verify term is included due to sufficient frequency and growth
        assert len(result) == 1
        assert result[0]["term"] == "term3"
        assert result[0]["total_mentions"] == 6
        assert result[0]["growth_rate"] > 0.5
        
        # Test case 4: Term appears in both first and last period but with total frequency < 3
        trend_data = {
            "2023-05-01": [("term4", 1)],
            "2023-05-02": [("term4", 0)],
            "2023-05-03": [("term4", 1)]  # term4 appears in first and last period but only twice total
        }
        
        result = analyzer._detect_trends(trend_data)
        
        # Verify term is filtered out due to insufficient total frequency
        assert len(result) == 0

    def test_noise_filtering(self, analyzer: HeadlineTrendAnalyzer, caplog) -> None:
        """Test the noise filtering logic in trend detection.
        
        This test focuses specifically on the logic that filters out terms
        with insufficient total mentions across all periods.
        """
        # Setup test data with a mix of noisy and significant terms
        trend_data = {
            "2023-05-01": [
                ("noisy_term", 1),      # Will have 2 total mentions
                ("valid_term", 2),       # Will have 4 total mentions
            ],
            "2023-05-02": [
                ("noisy_term", 1),
                ("valid_term", 2),
            ],
            "2023-05-03": [
                ("noisy_term", 0),
                ("valid_term", 0),
            ]
        }
        
        # Enable debug logging to verify our filtering logic
        caplog.set_level(logging.DEBUG)
        
        # Run trend detection
        result = analyzer._detect_trends(trend_data)
        
        # Verify logging shows proper filtering
        assert any("Skipping term 'noisy_term' due to insufficient mentions" in record.message 
                  for record in caplog.records)
        
        # Verify noisy term was filtered out
        noisy_terms = [item["term"] for item in result]
        assert "noisy_term" not in noisy_terms
        
        # Clean up by resetting logging
        caplog.clear()

    def test_noise_filtering_comprehensive(self, analyzer: HeadlineTrendAnalyzer) -> None:
        """Test all branches of the noise filtering logic in trend detection."""
        # Case 1: Empty trend data
        result = analyzer._detect_trends({})
        assert result == []
        
        # Case 2: Single period (insufficient for trends)
        result = analyzer._detect_trends({
            "2023-05-01": [("term1", 1)]
        })
        assert result == []
        
        # Case 3: Term with < 3 total mentions
        result = analyzer._detect_trends({
            "2023-05-01": [("term1", 1)],
            "2023-05-02": [("term1", 1)],
            "2023-05-03": [("term1", 0)]
        })
        assert result == []
        
        # Case 4: Term with exactly 3 mentions but no growth
        result = analyzer._detect_trends({
            "2023-05-01": [("term2", 1)],
            "2023-05-02": [("term2", 1)],
            "2023-05-03": [("term2", 1)]
        })
        assert result == []
        
        # Case 5: Term with > 3 mentions and significant growth
        result = analyzer._detect_trends({
            "2023-05-01": [("term3", 1)],
            "2023-05-02": [("term3", 2)],
            "2023-05-03": [("term3", 3)]
        })
        assert len(result) == 1
        assert result[0]["term"] == "term3"
        assert result[0]["growth_rate"] > 0.5
        
        # Case 6: Multiple terms with different characteristics
        result = analyzer._detect_trends({
            "2023-05-01": [
                ("low_freq", 1),     # Will have < 3 mentions
                ("no_growth", 2),    # Will have >= 3 mentions but no growth
                ("growing", 1)       # Will have >= 3 mentions and growth
            ],
            "2023-05-02": [
                ("low_freq", 1),
                ("no_growth", 2),
                ("growing", 2)
            ],
            "2023-05-03": [
                ("low_freq", 0),
                ("no_growth", 2),
                ("growing", 3)
            ]
        })
        
        # Verify results
        assert len(result) == 1
        assert result[0]["term"] == "growing"
        assert result[0]["growth_rate"] > 0.5
        assert result[0]["total_mentions"] >= 3
