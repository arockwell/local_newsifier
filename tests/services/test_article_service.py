"""Tests for the ArticleService."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


@pytest.mark.skip(
    reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR"
)
def test_process_article():
    """Test the complete article processing flow using the service."""
    # Arrange
    # Mock the entity service
    mock_entity_service = MagicMock()
    mock_entity_service.process_article_entities.return_value = [
        {
            "original_text": "John Doe",
            "canonical_name": "John Doe",
            "canonical_id": 1,
            "canonical_type": "PERSON",
            "context": "John Doe visited the city.",
            "sentiment_score": 0.5,
            "framing_category": "neutral",
        }
    ]

    # Mock CRUD operations
    mock_article_crud = MagicMock()
    mock_article_crud.create.return_value = MagicMock(
        id=1, title="Test Article", url="https://example.com"
    )

    mock_analysis_result_crud = MagicMock()
    mock_analysis_result_crud.create.return_value = MagicMock(id=1)

    # Mock session manager
    mock_session_manager = MagicMock()
    mock_session = MagicMock()
    mock_session_manager.return_value.__enter__.return_value = mock_session

    # Create the service with mocks
    from local_newsifier.services.article_service import ArticleService

    service = ArticleService(
        article_crud=mock_article_crud,
        analysis_result_crud=mock_analysis_result_crud,
        entity_service=mock_entity_service,
        session_factory=lambda: mock_session_manager(),
    )

    # Act
    result = service.process_article(
        url="https://example.com",
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Assert
    # Verify entity service was called correctly
    mock_entity_service.process_article_entities.assert_called_once_with(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1),
    )

    # Verify CRUD operations
    mock_article_crud.create.assert_called_once()
    mock_analysis_result_crud.create.assert_called_once()

    # Verify result
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"
    assert len(result["entities"]) == 1
    assert result["entities"][0]["original_text"] == "John Doe"
    assert result["analysis_result"]["statistics"]["total_entities"] == 1


@pytest.mark.skip(
    reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR"
)
def test_get_article():
    """Test retrieving an article with its analysis results."""
    # Arrange
    # Mock CRUD operations
    mock_article_crud = MagicMock()
    mock_article_crud.get.return_value = MagicMock(
        id=1,
        title="Test Article",
        url="https://example.com",
        content="Test content",
        published_at=datetime(2025, 1, 1),
        status="analyzed",
    )

    mock_analysis_result_crud = MagicMock()
    mock_analysis_result_crud.get_by_article.return_value = [
        MagicMock(
            id=1,
            article_id=1,
            analysis_type="entity_analysis",
            results={
                "entities": [
                    {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1}
                ],
                "statistics": {"total_entities": 1},
            },
        )
    ]

    # Mock session manager
    mock_session_manager = MagicMock()
    mock_session = MagicMock()
    mock_session_manager.return_value.__enter__.return_value = mock_session

    # Create the service with mocks
    from local_newsifier.services.article_service import ArticleService

    service = ArticleService(
        article_crud=mock_article_crud,
        analysis_result_crud=mock_analysis_result_crud,
        entity_service=MagicMock(),
        session_factory=lambda: mock_session_manager(),
    )

    # Act
    result = service.get_article(1)

    # Assert
    # Verify CRUD operations
    mock_article_crud.get.assert_called_once_with(mock_session, id=1)
    mock_analysis_result_crud.get_by_article.assert_called_once_with(mock_session, article_id=1)

    # Verify result
    assert result["article_id"] == 1
    assert result["title"] == "Test Article"
    assert result["url"] == "https://example.com"
    assert result["content"] == "Test content"
    assert len(result["analysis_results"]) == 1
    assert result["analysis_results"][0]["statistics"]["total_entities"] == 1


@pytest.mark.skip(
    reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR"
)
def test_get_article_not_found():
    """Test retrieving a non-existent article."""
    # Arrange
    # Mock CRUD operations
    mock_article_crud = MagicMock()
    mock_article_crud.get.return_value = None

    # Mock session manager
    mock_session_manager = MagicMock()
    mock_session = MagicMock()
    mock_session_manager.return_value.__enter__.return_value = mock_session

    # Create the service with mocks
    from local_newsifier.services.article_service import ArticleService

    service = ArticleService(
        article_crud=mock_article_crud,
        analysis_result_crud=MagicMock(),
        entity_service=MagicMock(),
        session_factory=lambda: mock_session_manager(),
    )

    # Act
    result = service.get_article(999)

    # Assert
    assert result is None
