"""Test fixtures for CRUD module tests."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from local_newsifier.models.database.base import Base
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.database.analysis_result import AnalysisResultDB
from local_newsifier.models.entity_tracking import (
    CanonicalEntityDB, EntityMentionContextDB, EntityProfileDB, 
    entity_mentions, entity_relationships
)


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    session_factory = sessionmaker(bind=db_engine)
    session = session_factory()
    yield session
    session.close()


@pytest.fixture(scope="function")
def sample_article_data():
    """Sample article data for testing."""
    return {
        "title": "Test Article",
        "content": "This is a test article.",
        "url": "https://example.com/test-article",
        "source": "test_source",
        "published_at": datetime.now(timezone.utc),
        "status": "new",
        "scraped_at": datetime.now(timezone.utc)
    }


@pytest.fixture(scope="function")
def sample_entity_data():
    """Sample entity data for testing."""
    return {
        "article_id": 1,
        "text": "Test Entity",
        "entity_type": "TEST",
        "confidence": 0.95,
        "sentence_context": "This is a test entity context."
    }


@pytest.fixture(scope="function")
def sample_analysis_result_data():
    """Sample analysis result data for testing."""
    return {
        "article_id": 1,
        "analysis_type": "test_analysis",
        "results": {"key": "value"}
    }


@pytest.fixture(scope="function")
def sample_canonical_entity_data():
    """Sample canonical entity data for testing."""
    return {
        "name": "Test Canonical Entity",
        "entity_type": "PERSON",
        "description": "This is a test canonical entity.",
        "entity_metadata": {"key": "value"}
    }


@pytest.fixture(scope="function")
def sample_entity_mention_context_data():
    """Sample entity mention context data for testing."""
    return {
        "entity_id": 1,
        "article_id": 1,
        "context_text": "This is a test context for entity mentions.",
        "context_type": "sentence",
        "sentiment_score": 0.8
    }


@pytest.fixture(scope="function")
def sample_entity_profile_data():
    """Sample entity profile data for testing."""
    return {
        "canonical_entity_id": 1,
        "profile_type": "summary",
        "content": "This is a test profile content.",
        "profile_metadata": {"key": "value"}
    }


@pytest.fixture(scope="function")
def sample_entity_relationship_data():
    """Sample entity relationship data for testing."""
    return {
        "source_entity_id": 1,
        "target_entity_id": 2,
        "relationship_type": "RELATED_TO",
        "confidence": 0.9,
        "evidence": "This is evidence for the relationship."
    }


@pytest.fixture(scope="function")
def create_article(db_session):
    """Create a test article in the database."""
    article = ArticleDB(
        title="Test Article",
        content="This is a test article.",
        url="https://example.com/test-article",
        source="test_source",
        published_at=datetime.now(timezone.utc),
        status="new",
        scraped_at=datetime.now(timezone.utc)
    )
    db_session.add(article)
    db_session.commit()
    return article


@pytest.fixture(scope="function")
def create_entity(db_session, create_article):
    """Create a test entity in the database."""
    entity = EntityDB(
        article_id=create_article.id,
        text="Test Entity",
        entity_type="TEST",
        confidence=0.95,
        sentence_context="This is a test entity context."
    )
    db_session.add(entity)
    db_session.commit()
    return entity


@pytest.fixture(scope="function")
def create_canonical_entity(db_session):
    """Create a test canonical entity in the database."""
    entity = CanonicalEntityDB(
        name="Test Canonical Entity",
        entity_type="PERSON",
        description="This is a test canonical entity.",
        entity_metadata={"key": "value"}
    )
    db_session.add(entity)
    db_session.commit()
    return entity


@pytest.fixture(scope="function")
def create_canonical_entities(db_session):
    """Create multiple test canonical entities in the database."""
    entities = [
        CanonicalEntityDB(
            name="Test Entity 1",
            entity_type="PERSON",
            description="This is test entity 1",
            entity_metadata={"id": 1}
        ),
        CanonicalEntityDB(
            name="Test Entity 2",
            entity_type="ORG",
            description="This is test entity 2",
            entity_metadata={"id": 2}
        ),
        CanonicalEntityDB(
            name="Test Entity 3",
            entity_type="PERSON",
            description="This is test entity 3",
            entity_metadata={"id": 3}
        )
    ]
    for entity in entities:
        db_session.add(entity)
    db_session.commit()
    return entities