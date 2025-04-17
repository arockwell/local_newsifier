"""Tests for the analysis result CRUD module."""

from sqlmodel import select

from local_newsifier.crud.analysis_result import CRUDAnalysisResult
from local_newsifier.crud.analysis_result import (
    analysis_result as analysis_result_crud,
)
from local_newsifier.models.database.analysis_result import AnalysisResult


class TestAnalysisResultCRUD:
    """Tests for AnalysisResultCRUD class."""

    def test_create(
        self, db_session, create_article, sample_analysis_result_data
    ):
        """Test creating a new analysis result."""
        result = analysis_result_crud.create(db_session, obj_in=sample_analysis_result_data)

        assert result is not None
        assert result.id is not None
        assert result.article_id == sample_analysis_result_data["article_id"]
        assert result.analysis_type == sample_analysis_result_data["analysis_type"]
        assert result.results == sample_analysis_result_data["results"]

        # Verify it was saved to the database
        db_result = (
            db_session.exec(select(AnalysisResult))
            .filter(AnalysisResult.id == result.id)
            .first()
        )
        assert db_result is not None
        assert db_result.analysis_type == sample_analysis_result_data["analysis_type"]

    def test_get(
        self, db_session, create_article, sample_analysis_result_data
    ):
        """Test getting an analysis result by ID."""
        # Create an analysis result
        db_result = AnalysisResult(**sample_analysis_result_data)
        db_session.add(db_result)
        db_session.commit()

        # Test getting the result by ID
        result = analysis_result_crud.get(db_session, id=db_result.id)

        assert result is not None
        assert result.id == db_result.id
        assert result.article_id == db_result.article_id
        assert result.analysis_type == db_result.analysis_type
        assert result.results == db_result.results

    def test_get_by_article(self, db_session, create_article):
        """Test getting analysis results by article ID."""
        # Create multiple analysis results for the same article
        results_data = [
            {
                "article_id": create_article.id,
                "analysis_type": "sentiment",
                "results": {"sentiment": "positive", "score": 0.8},
            },
            {
                "article_id": create_article.id,
                "analysis_type": "topic",
                "results": {"topics": ["tech", "science"], "confidence": 0.9},
            },
            {
                "article_id": create_article.id,
                "analysis_type": "entity",
                "results": {"entities": ["Apple", "Google"], "count": 2},
            },
        ]

        for result_data in results_data:
            db_result = AnalysisResult(**result_data)
            db_session.add(db_result)
        db_session.commit()

        # Test getting all analysis results for the article
        results = analysis_result_crud.get_by_article(
            db_session, article_id=create_article.id
        )

        assert len(results) == 3
        analysis_types = [result.analysis_type for result in results]
        assert "sentiment" in analysis_types
        assert "topic" in analysis_types
        assert "entity" in analysis_types

    def test_get_by_article_empty(self, db_session, create_article):
        """Test getting analysis results for an article with no results."""
        results = analysis_result_crud.get_by_article(
            db_session, article_id=create_article.id
        )

        assert len(results) == 0

    def test_get_by_article_and_type(self, db_session, create_article):
        """Test getting an analysis result by article ID and type."""
        # Create multiple analysis results for the same article
        results_data = [
            {
                "article_id": create_article.id,
                "analysis_type": "sentiment",
                "results": {"sentiment": "positive", "score": 0.8},
            },
            {
                "article_id": create_article.id,
                "analysis_type": "topic",
                "results": {"topics": ["tech", "science"], "confidence": 0.9},
            },
            {
                "article_id": create_article.id,
                "analysis_type": "entity",
                "results": {"entities": ["Apple", "Google"], "count": 2},
            },
        ]

        for result_data in results_data:
            db_result = AnalysisResult(**result_data)
            db_session.add(db_result)
        db_session.commit()

        # Test getting a specific analysis result by type
        result = analysis_result_crud.get_by_article_and_type(
            db_session, article_id=create_article.id, analysis_type="sentiment"
        )

        assert result is not None
        assert result.article_id == create_article.id
        assert result.analysis_type == "sentiment"
        assert result.results == {"sentiment": "positive", "score": 0.8}

    def test_get_by_article_and_type_not_found(
        self, db_session, create_article
    ):
        """Test getting non-existent analysis result."""
        result = analysis_result_crud.get_by_article_and_type(
            db_session,
            article_id=create_article.id,
            analysis_type="nonexistent",
        )

        assert result is None

    def test_singleton_instance(self):
        """Test singleton instance behavior."""
        assert isinstance(analysis_result_crud, CRUDAnalysisResult)
        assert analysis_result_crud.model == AnalysisResult
