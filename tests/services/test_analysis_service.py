"""Tests for the analysis_service module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.trend import TrendAnalysis, TrendType


class TestAnalysisService:
    """Tests for the AnalysisService class."""

    @pytest.fixture
    def mock_session(self):
        """Return a mock database session."""
        session = MagicMock()
        session.__enter__ = MagicMock(return_value=session)
        session.__exit__ = MagicMock(return_value=None)
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Return a mock session factory that returns the mock session."""
        return MagicMock(return_value=mock_session)

    @pytest.fixture
    def mock_article_crud(self):
        """Return a mock article CRUD component."""
        return MagicMock()

    @pytest.fixture
    def mock_entity_crud(self):
        """Return a mock entity CRUD component."""
        return MagicMock()

    @pytest.fixture
    def mock_analysis_result_crud(self):
        """Return a mock analysis result CRUD component."""
        return MagicMock()

    @pytest.fixture
    def mock_trend_analyzer(self):
        """Return a mock trend analyzer."""
        return MagicMock()

    def _create_service(
        self,
        mock_analysis_result_crud,
        mock_article_crud,
        mock_entity_crud,
        mock_trend_analyzer,
        mock_session_factory,
    ):
        """Helper method to create an AnalysisService with mocks."""
        # Import here to ensure patch is applied first
        from local_newsifier.services.analysis_service import AnalysisService

        return AnalysisService(
            analysis_result_crud=mock_analysis_result_crud,
            article_crud=mock_article_crud,
            entity_crud=mock_entity_crud,
            trend_analyzer=mock_trend_analyzer,
            session_factory=mock_session_factory,
        )

    @pytest.fixture
    def sample_articles(self):
        """Return a list of sample articles."""
        now = datetime.now(timezone.utc)
        return [
            Article(
                id=1,
                url="http://example.com/1",
                title="Gainesville mayor announces new initiative",
                content="The mayor of Gainesville announced a new initiative today.",
                published_at=now - timedelta(days=1),
            ),
            Article(
                id=2,
                url="http://example.com/2",
                title="Mayor discusses budget plans",
                content="Mayor discusses new budget plans for the city.",
                published_at=now - timedelta(days=2),
            ),
        ]

    @pytest.fixture
    def sample_entities(self):
        """Return a list of sample entities."""
        return [
            Entity(
                id=1,
                article_id=1,
                text="Mayor",
                entity_type="PERSON",
                sentence_context="The mayor of Gainesville announced a new initiative today.",
            ),
            Entity(
                id=2,
                article_id=2,
                text="Mayor",
                entity_type="PERSON",
                sentence_context="Mayor discusses new budget plans for the city.",
            ),
        ]

    @patch("fastapi_injectable.concurrency.run_coroutine_sync")
    def test_analyze_headline_trends(
        self,
        mock_run_coroutine,
        mock_session,
        mock_analysis_result_crud,
        mock_article_crud,
        mock_entity_crud,
        mock_trend_analyzer,
        mock_session_factory,
        sample_articles,
    ):
        """Test analysis of headline trends."""
        # Setup mock to avoid actual asyncio operations
        mock_run_coroutine.return_value = []

        # Create the service with mocks
        service = self._create_service(
            mock_analysis_result_crud,
            mock_article_crud,
            mock_entity_crud,
            mock_trend_analyzer,
            mock_session_factory,
        )

        # Setup mocks
        mock_article_crud.get_by_date_range.return_value = sample_articles
        mock_trend_analyzer.extract_keywords.return_value = [("mayor", 2), ("city", 1)]
        mock_trend_analyzer.detect_keyword_trends.return_value = [
            {
                "term": "mayor",
                "growth_rate": 1.0,
                "first_count": 1,
                "last_count": 2,
                "total_mentions": 3,
            }
        ]

        # Patch any async methods if they exist
        if hasattr(service, "analyze_headline_trends_async"):
            service.analyze_headline_trends_async = AsyncMock()

        # Call the method
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        result = service.analyze_headline_trends(start_date, end_date)

        # Verify the result
        assert "trending_terms" in result
        assert "overall_top_terms" in result
        assert "raw_data" in result
        assert "period_counts" in result

        # Verify the mocks were called
        mock_article_crud.get_by_date_range.assert_called_once_with(
            mock_session, start_date=start_date, end_date=end_date
        )
        mock_trend_analyzer.extract_keywords.assert_called()
        mock_trend_analyzer.detect_keyword_trends.assert_called_once()

    @patch("fastapi_injectable.concurrency.run_coroutine_sync")
    def test_analyze_headline_trends_empty(
        self,
        mock_run_coroutine,
        mock_session,
        mock_analysis_result_crud,
        mock_article_crud,
        mock_entity_crud,
        mock_trend_analyzer,
        mock_session_factory,
    ):
        """Test analysis of headline trends with no articles."""
        # Setup mock to avoid actual asyncio operations
        mock_run_coroutine.return_value = []

        # Create the service with mocks
        service = self._create_service(
            mock_analysis_result_crud,
            mock_article_crud,
            mock_entity_crud,
            mock_trend_analyzer,
            mock_session_factory,
        )

        # Setup mocks
        mock_article_crud.get_by_date_range.return_value = []

        # Patch any async methods if they exist
        if hasattr(service, "analyze_headline_trends_async"):
            service.analyze_headline_trends_async = AsyncMock()

        # Call the method
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        result = service.analyze_headline_trends(start_date, end_date)

        # Verify the result
        assert "error" in result
        assert result["error"] == "No headlines found in the specified period"

    @patch("fastapi_injectable.concurrency.run_coroutine_sync")
    def test_detect_entity_trends(
        self,
        mock_run_coroutine,
        mock_session,
        mock_analysis_result_crud,
        mock_entity_crud,
        mock_article_crud,
        mock_trend_analyzer,
        mock_session_factory,
        sample_entities,
        sample_articles,
    ):
        """Test detection of entity trends."""
        # Setup mock to avoid actual asyncio operations
        mock_run_coroutine.return_value = []

        # Create the service with mocks
        service = self._create_service(
            mock_analysis_result_crud,
            mock_article_crud,
            mock_entity_crud,
            mock_trend_analyzer,
            mock_session_factory,
        )
        # Setup mocks
        mock_entity_crud.get_by_date_range_and_types.return_value = sample_entities
        mock_article_crud.get_by_date_range.return_value = sample_articles

        sample_trend = TrendAnalysis(
            trend_type=TrendType.FREQUENCY_SPIKE,
            name="Mayor (PERSON)",
            description="Significant increase in mentions of person 'Mayor'",
            confidence_score=0.8,
            start_date=datetime.now(timezone.utc),
        )
        mock_trend_analyzer.detect_entity_trends.return_value = [sample_trend]

        # Patch any async methods if they exist
        if hasattr(service, "detect_entity_trends_async"):
            service.detect_entity_trends_async = AsyncMock()

        # Call the method
        result = service.detect_entity_trends(entity_types=["PERSON", "ORG", "GPE"])

        # Verify the result
        assert len(result) == 1
        assert result[0].name == "Mayor (PERSON)"
        assert result[0].trend_type == TrendType.FREQUENCY_SPIKE

        # Verify the mocks were called
        mock_entity_crud.get_by_date_range_and_types.assert_called_once()
        mock_article_crud.get_by_date_range.assert_called_once()
        mock_trend_analyzer.detect_entity_trends.assert_called_once()

    @patch("fastapi_injectable.concurrency.run_coroutine_sync")
    def test_save_analysis_result(
        self,
        mock_run_coroutine,
        mock_session,
        mock_analysis_result_crud,
        mock_article_crud,
        mock_entity_crud,
        mock_trend_analyzer,
        mock_session_factory,
    ):
        """Test saving an analysis result."""
        # Setup mock to avoid actual asyncio operations
        mock_run_coroutine.return_value = []

        # Create the service with mocks
        service = self._create_service(
            mock_analysis_result_crud,
            mock_article_crud,
            mock_entity_crud,
            mock_trend_analyzer,
            mock_session_factory,
        )
        # Setup mock for non-existing result
        mock_analysis_result_crud.get_by_article_and_type.return_value = None

        # Call the method
        article_id = 1
        analysis_type = "headline_trend"
        results = {"trending_terms": [{"term": "mayor", "growth_rate": 1.0}]}

        # Patch any async methods if they exist
        if hasattr(service, "_save_analysis_result_async"):
            service._save_analysis_result_async = AsyncMock()

        service._save_analysis_result(mock_session, article_id, analysis_type, results)

        # Verify the mock was called
        mock_analysis_result_crud.get_by_article_and_type.assert_called_once_with(
            mock_session, article_id=article_id, analysis_type=analysis_type
        )
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("fastapi_injectable.concurrency.run_coroutine_sync")
    def test_save_analysis_result_existing(
        self,
        mock_run_coroutine,
        mock_session,
        mock_analysis_result_crud,
        mock_article_crud,
        mock_entity_crud,
        mock_trend_analyzer,
        mock_session_factory,
    ):
        """Test updating an existing analysis result."""
        # Setup mock to avoid actual asyncio operations
        mock_run_coroutine.return_value = []

        # Create the service with mocks
        service = self._create_service(
            mock_analysis_result_crud,
            mock_article_crud,
            mock_entity_crud,
            mock_trend_analyzer,
            mock_session_factory,
        )
        # Setup mock for existing result
        existing_result = AnalysisResult(
            article_id=1,
            analysis_type="headline_trend",
            results={"trending_terms": [{"term": "school", "growth_rate": 0.5}]},
        )
        mock_analysis_result_crud.get_by_article_and_type.return_value = existing_result

        # Patch any async methods if they exist
        if hasattr(service, "_save_analysis_result_async"):
            service._save_analysis_result_async = AsyncMock()

        # Call the method
        article_id = 1
        analysis_type = "headline_trend"
        new_results = {"trending_terms": [{"term": "mayor", "growth_rate": 1.0}]}

        service._save_analysis_result(mock_session, article_id, analysis_type, new_results)

        # Verify the mock was called
        mock_analysis_result_crud.get_by_article_and_type.assert_called_once()
        # Verify the results were updated
        assert existing_result.results["trending_terms"] == [{"term": "mayor", "growth_rate": 1.0}]
        mock_session.add.assert_called_once_with(existing_result)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @patch("fastapi_injectable.concurrency.run_coroutine_sync")
    def test_get_analysis_result(
        self,
        mock_run_coroutine,
        mock_session,
        mock_analysis_result_crud,
        mock_article_crud,
        mock_entity_crud,
        mock_trend_analyzer,
        mock_session_factory,
    ):
        """Test getting an analysis result."""
        # Setup mock to avoid actual asyncio operations
        mock_run_coroutine.return_value = []

        # Create the service with mocks
        service = self._create_service(
            mock_analysis_result_crud,
            mock_article_crud,
            mock_entity_crud,
            mock_trend_analyzer,
            mock_session_factory,
        )
        # Setup mock
        expected_result = AnalysisResult(
            article_id=1,
            analysis_type="headline_trend",
            results={"trending_terms": [{"term": "mayor", "growth_rate": 1.0}]},
        )
        mock_analysis_result_crud.get_by_article_and_type.return_value = expected_result

        # Patch any async methods if they exist
        if hasattr(service, "get_analysis_result_async"):
            service.get_analysis_result_async = AsyncMock()

        # Call the method
        result = service.get_analysis_result(1, "headline_trend")

        # Verify the result
        assert result == expected_result.results
        assert result["trending_terms"] == [{"term": "mayor", "growth_rate": 1.0}]

        # Test with non-existing result
        mock_analysis_result_crud.get_by_article_and_type.return_value = None
        result = service.get_analysis_result(2, "entity_trend")
        assert result is None
