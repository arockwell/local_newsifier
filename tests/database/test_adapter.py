"""Tests for the database adapter module."""

import pytest
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.database.adapter import (
    create_article,
    get_article,
    get_article_by_url,
    update_article_status,
    get_articles_by_status,
    add_entity,
    get_entities_by_article,
    add_analysis_result,
    get_analysis_results_by_article,
)
from local_newsifier.models.pydantic_models import (
    ArticleCreate,
    EntityCreate,
    AnalysisResultCreate,
)


def test_create_article(db_session: Session):
    """Test creating an article with the adapter function."""
    # Arrange
    article_data = ArticleCreate(
        url="https://example.com/test",
        title="Test Article",
        content="Test content",
        published_at=datetime.now(timezone.utc),
        status="initialized",
    )

    # Act
    article = create_article(article_data, session=db_session)

    # Assert
    assert article.id is not None
    assert article.url == article_data.url
    assert article.title == article_data.title
    assert article.content == article_data.content
    assert article.status == article_data.status


def test_get_article(db_session: Session):
    """Test getting an article with the adapter function."""
    # Arrange
    article_data = ArticleCreate(
        url="https://example.com/test-get",
        title="Test Get Article",
        content="Test content for get",
        published_at=datetime.now(timezone.utc),
        status="initialized",
    )
    manager = DatabaseManager(db_session)
    created_article = manager.create_article(article_data)

    # Act
    article = get_article(created_article.id, session=db_session)

    # Assert
    assert article is not None
    assert article.id == created_article.id
    assert article.url == article_data.url
    assert article.title == article_data.title


def test_get_article_by_url(db_session: Session):
    """Test getting an article by URL with the adapter function."""
    # Arrange
    url = "https://example.com/test-get-by-url"
    article_data = ArticleCreate(
        url=url,
        title="Test Get Article By URL",
        content="Test content for get by URL",
        published_at=datetime.now(timezone.utc),
        status="initialized",
    )
    manager = DatabaseManager(db_session)
    manager.create_article(article_data)

    # Act
    article = get_article_by_url(url, session=db_session)

    # Assert
    assert article is not None
    assert article.url == url
    assert article.title == article_data.title


def test_update_article_status(db_session: Session):
    """Test updating an article status with the adapter function."""
    # Arrange
    article_data = ArticleCreate(
        url="https://example.com/test-update-status",
        title="Test Update Status",
        content="Test content for update status",
        published_at=datetime.now(timezone.utc),
        status="initialized",
    )
    manager = DatabaseManager(db_session)
    created_article = manager.create_article(article_data)

    # Act
    updated_article = update_article_status(
        created_article.id, "analyzed", session=db_session
    )

    # Assert
    assert updated_article is not None
    assert updated_article.id == created_article.id
    assert updated_article.status == "analyzed"


def test_get_articles_by_status(db_session: Session):
    """Test getting articles by status with the adapter function."""
    # Arrange
    status = "test_status"
    article_data1 = ArticleCreate(
        url="https://example.com/test-get-by-status-1",
        title="Test Get By Status 1",
        content="Test content for get by status 1",
        published_at=datetime.now(timezone.utc),
        status=status,
    )
    article_data2 = ArticleCreate(
        url="https://example.com/test-get-by-status-2",
        title="Test Get By Status 2",
        content="Test content for get by status 2",
        published_at=datetime.now(timezone.utc),
        status=status,
    )
    manager = DatabaseManager(db_session)
    manager.create_article(article_data1)
    manager.create_article(article_data2)

    # Act
    articles = get_articles_by_status(status, session=db_session)

    # Assert
    assert isinstance(articles, list)
    assert len(articles) >= 2
    assert all(article.status == status for article in articles)


def test_add_entity(db_session: Session):
    """Test adding an entity with the adapter function."""
    # Arrange
    article_data = ArticleCreate(
        url="https://example.com/test-add-entity",
        title="Test Add Entity",
        content="Test content for add entity",
        published_at=datetime.now(timezone.utc),
        status="initialized",
    )
    manager = DatabaseManager(db_session)
    created_article = manager.create_article(article_data)

    entity_data = EntityCreate(
        article_id=created_article.id,
        text="Test Entity",
        entity_type="PERSON",
        confidence=0.9,
    )

    # Act
    entity = add_entity(entity_data, session=db_session)

    # Assert
    assert entity.id is not None
    assert entity.article_id == created_article.id
    assert entity.text == entity_data.text
    assert entity.entity_type == entity_data.entity_type
    assert entity.confidence == entity_data.confidence


def test_get_entities_by_article(db_session: Session):
    """Test getting entities by article with the adapter function."""
    # Arrange
    article_data = ArticleCreate(
        url="https://example.com/test-get-entities",
        title="Test Get Entities",
        content="Test content for get entities",
        published_at=datetime.now(timezone.utc),
        status="initialized",
    )
    manager = DatabaseManager(db_session)
    created_article = manager.create_article(article_data)

    entity_data1 = EntityCreate(
        article_id=created_article.id,
        text="Test Entity 1",
        entity_type="PERSON",
        confidence=0.9,
    )
    entity_data2 = EntityCreate(
        article_id=created_article.id,
        text="Test Entity 2",
        entity_type="ORG",
        confidence=0.8,
    )
    manager.add_entity(entity_data1)
    manager.add_entity(entity_data2)

    # Act
    entities = get_entities_by_article(created_article.id, session=db_session)

    # Assert
    assert isinstance(entities, list)
    assert len(entities) >= 2
    assert all(entity.article_id == created_article.id for entity in entities)


def test_add_analysis_result(db_session: Session):
    """Test adding an analysis result with the adapter function."""
    # Arrange
    article_data = ArticleCreate(
        url="https://example.com/test-add-result",
        title="Test Add Result",
        content="Test content for add result",
        published_at=datetime.now(timezone.utc),
        status="initialized",
    )
    manager = DatabaseManager(db_session)
    created_article = manager.create_article(article_data)

    result_data = AnalysisResultCreate(
        article_id=created_article.id,
        analysis_type="SENTIMENT",
        result={"sentiment": "positive", "score": 0.8},
    )

    # Act
    result = add_analysis_result(result_data, session=db_session)

    # Assert
    assert result.id is not None
    assert result.article_id == created_article.id
    assert result.analysis_type == result_data.analysis_type
    assert result.result == result_data.result


def test_get_analysis_results_by_article(db_session: Session):
    """Test getting analysis results by article with the adapter function."""
    # Arrange
    article_data = ArticleCreate(
        url="https://example.com/test-get-results",
        title="Test Get Results",
        content="Test content for get results",
        published_at=datetime.now(timezone.utc),
        status="initialized",
    )
    manager = DatabaseManager(db_session)
    created_article = manager.create_article(article_data)

    result_data1 = AnalysisResultCreate(
        article_id=created_article.id,
        analysis_type="SENTIMENT",
        result={"sentiment": "positive", "score": 0.8},
    )
    result_data2 = AnalysisResultCreate(
        article_id=created_article.id,
        analysis_type="TOPIC",
        result={"topic": "politics", "confidence": 0.9},
    )
    manager.add_analysis_result(result_data1)
    manager.add_analysis_result(result_data2)

    # Act
    results = get_analysis_results_by_article(created_article.id, session=db_session)

    # Assert
    assert isinstance(results, list)
    assert len(results) >= 2
    assert all(result.article_id == created_article.id for result in results)