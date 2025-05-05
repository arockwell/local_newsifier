"""Test configuration and fixtures for all tests.

This module provides common test fixtures like sample data.
Database configuration is handled in the root conftest.py.
"""

from datetime import datetime, timezone
import os
from typing import Dict, List, Generator

import pytest
from sqlmodel import Session

# Import model classes only for type hints
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, EntityMention, EntityMentionContext,
    EntityProfile, EntityRelationship
)

# Note: We don't need to register models here as it's done in root conftest.py

# ==================== Sample Data Fixtures ====================

@pytest.fixture(scope="function")
def sample_article_data() -> Dict:
    """Sample article data for testing."""
    return {
        "title": "Test Article",
        "content": "This is a test article.",
        "url": "https://example.com/test-article",
        "source": "test_source",
        "published_at": datetime.now(timezone.utc),
        "status": "new",
        "scraped_at": datetime.now(timezone.utc),
    }


@pytest.fixture(scope="function")
def sample_entity_data() -> Dict:
    """Sample entity data for testing."""
    return {
        "article_id": 1,
        "text": "Test Entity",
        "entity_type": "TEST",
        "confidence": 0.95,
        "sentence_context": "This is a test entity context.",
    }


@pytest.fixture(scope="function")
def sample_analysis_result_data() -> Dict:
    """Sample analysis result data for testing."""
    return {
        "article_id": 1,
        "analysis_type": "test_analysis",
        "results": {"key": "value"},
    }


@pytest.fixture(scope="function")
def sample_canonical_entity_data() -> Dict:
    """Sample canonical entity data for testing."""
    return {
        "name": "Test Canonical Entity",
        "entity_type": "PERSON",
        "description": "This is a test canonical entity.",
        "entity_metadata": {"key": "value"},
    }


@pytest.fixture(scope="function")
def sample_entity_mention_context_data() -> Dict:
    """Sample entity mention context data for testing."""
    return {
        "entity_id": 1,
        "article_id": 1,
        "context_text": "This is a test context for entity mentions.",
        "context_type": "sentence",
        "sentiment_score": 0.8,
    }


@pytest.fixture(scope="function")
def sample_entity_profile_data() -> Dict:
    """Sample entity profile data for testing."""
    return {
        "canonical_entity_id": 1,
        "profile_type": "summary",
        "content": "This is a test profile content.",
        "profile_metadata": {"key": "value"},
    }


@pytest.fixture(scope="function")
def sample_apify_source_config_data() -> Dict:
    """Sample Apify source configuration data for testing."""
    return {
        "name": "Test News Source",
        "actor_id": "abc123",
        "is_active": True,
        "schedule": "0 * * * *",  # Run hourly
        "source_type": "news",
        "source_url": "https://example.com/news",
        "input_configuration": {
            "startUrls": [{"url": "https://example.com/news"}],
            "maxPagesPerCrawl": 10
        }
    }


@pytest.fixture(scope="function")
def sample_entity_relationship_data() -> Dict:
    """Sample entity relationship data for testing."""
    return {
        "source_entity_id": 1,
        "target_entity_id": 2,
        "relationship_type": "RELATED_TO",
        "confidence": 0.9,
        "evidence": "This is evidence for the relationship.",
    }

# ==================== Database Entity Creation Fixtures ====================

@pytest.fixture(scope="function")
def create_article(db_session) -> Article:
    """Create a test article in the database."""
    article = Article(
        title="Test Article",
        content="This is a test article.",
        url="https://example.com/test-article",
        source="test_source",
        published_at=datetime.now(timezone.utc),
        status="new",
        scraped_at=datetime.now(timezone.utc),
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


@pytest.fixture(scope="function")
def create_entity(db_session, create_article) -> Entity:
    """Create a test entity in the database."""
    entity = Entity(
        article_id=create_article.id,
        text="Test Entity",
        entity_type="TEST",
        confidence=0.95,
        sentence_context="This is a test entity context.",
    )
    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)
    return entity


@pytest.fixture(scope="function")
def create_canonical_entity(db_session) -> CanonicalEntity:
    """Create a test canonical entity in the database."""
    entity = CanonicalEntity(
        name="Test Canonical Entity",
        entity_type="PERSON",
        description="This is a test canonical entity.",
        entity_metadata={"key": "value"},
    )
    db_session.add(entity)
    db_session.commit()
    db_session.refresh(entity)
    return entity


@pytest.fixture(scope="function")
def create_canonical_entities(db_session) -> List[CanonicalEntity]:
    """Create multiple test canonical entities in the database."""
    entities = [
        CanonicalEntity(
            name="Test Entity 1",
            entity_type="PERSON",
            description="This is test entity 1",
            entity_metadata={"id": 1},
        ),
        CanonicalEntity(
            name="Test Entity 2",
            entity_type="ORG",
            description="This is test entity 2",
            entity_metadata={"id": 2},
        ),
        CanonicalEntity(
            name="Test Entity 3",
            entity_type="PERSON",
            description="This is test entity 3",
            entity_metadata={"id": 3},
        ),
    ]
    for entity in entities:
        db_session.add(entity)
    db_session.commit()
    for entity in entities:
        db_session.refresh(entity)
    return entities
