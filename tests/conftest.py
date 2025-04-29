"""Test configuration and fixtures for all tests.

This module provides fixtures that are specific to the tests directory.
Global fixtures are defined in the root conftest.py.
"""

from datetime import datetime, timezone
import os
import logging
from typing import Dict, List, Generator, Any

import pytest
from sqlmodel import Session

# Configure logging
logger = logging.getLogger(__name__)

# Import all fixtures and utilities from the root conftest.py
# They are automatically available to all tests
from conftest import *

# ==================== Legacy Sample Data Fixtures ====================
# These fixtures are kept for backward compatibility
# New tests should use the factory-based fixtures instead

@pytest.fixture(scope="function")
def sample_article_data() -> Dict:
    """Sample article data for testing.
    
    DEPRECATED: Use ArticleFactory instead.
    """
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
    """Sample entity data for testing.
    
    DEPRECATED: Use EntityFactory instead.
    """
    return {
        "article_id": 1,
        "text": "Test Entity",
        "entity_type": "TEST",
        "confidence": 0.95,
        "sentence_context": "This is a test entity context.",
    }

@pytest.fixture(scope="function")
def sample_analysis_result_data() -> Dict:
    """Sample analysis result data for testing.
    
    DEPRECATED: Use AnalysisResultFactory instead.
    """
    return {
        "article_id": 1,
        "analysis_type": "test_analysis",
        "results": {"key": "value"},
    }

@pytest.fixture(scope="function")
def sample_canonical_entity_data() -> Dict:
    """Sample canonical entity data for testing.
    
    DEPRECATED: Use CanonicalEntityFactory instead.
    """
    return {
        "name": "Test Canonical Entity",
        "entity_type": "PERSON",
        "description": "This is a test canonical entity.",
        "entity_metadata": {"key": "value"},
    }

@pytest.fixture(scope="function")
def sample_entity_mention_context_data() -> Dict:
    """Sample entity mention context data for testing.
    
    DEPRECATED: Use EntityMentionContextFactory instead.
    """
    return {
        "entity_id": 1,
        "article_id": 1,
        "context_text": "This is a test context for entity mentions.",
        "context_type": "sentence",
        "sentiment_score": 0.8,
    }

@pytest.fixture(scope="function")
def sample_entity_profile_data() -> Dict:
    """Sample entity profile data for testing.
    
    DEPRECATED: Use EntityProfileFactory instead.
    """
    return {
        "canonical_entity_id": 1,
        "profile_type": "summary",
        "content": "This is a test profile content.",
        "profile_metadata": {"key": "value"},
    }

@pytest.fixture(scope="function")
def sample_entity_relationship_data() -> Dict:
    """Sample entity relationship data for testing.
    
    DEPRECATED: Use EntityRelationshipFactory instead.
    """
    return {
        "source_entity_id": 1,
        "target_entity_id": 2,
        "relationship_type": "RELATED_TO",
        "confidence": 0.9,
        "evidence": "This is evidence for the relationship.",
    }

# ==================== Legacy Database Entity Creation Fixtures ====================
# These fixtures are kept for backward compatibility
# New tests should use the factory-based fixtures instead

@pytest.fixture(scope="function")
def create_article(db_function_session) -> Article:
    """Create a test article in the database.
    
    DEPRECATED: Use ArticleFactory instead.
    """
    logger.warning("create_article fixture is deprecated, use ArticleFactory instead")
    article = Article(
        title="Test Article",
        content="This is a test article.",
        url="https://example.com/test-article",
        source="test_source",
        published_at=datetime.now(timezone.utc),
        status="new",
        scraped_at=datetime.now(timezone.utc),
    )
    db_function_session.add(article)
    db_function_session.commit()
    db_function_session.refresh(article)
    return article

@pytest.fixture(scope="function")
def create_entity(db_function_session, create_article) -> Entity:
    """Create a test entity in the database.
    
    DEPRECATED: Use EntityFactory instead.
    """
    logger.warning("create_entity fixture is deprecated, use EntityFactory instead")
    entity = Entity(
        article_id=create_article.id,
        text="Test Entity",
        entity_type="TEST",
        confidence=0.95,
        sentence_context="This is a test entity context.",
    )
    db_function_session.add(entity)
    db_function_session.commit()
    db_function_session.refresh(entity)
    return entity

@pytest.fixture(scope="function")
def create_canonical_entity(db_function_session) -> CanonicalEntity:
    """Create a test canonical entity in the database.
    
    DEPRECATED: Use CanonicalEntityFactory instead.
    """
    logger.warning("create_canonical_entity fixture is deprecated, use CanonicalEntityFactory instead")
    entity = CanonicalEntity(
        name="Test Canonical Entity",
        entity_type="PERSON",
        description="This is a test canonical entity.",
        entity_metadata={"key": "value"},
    )
    db_function_session.add(entity)
    db_function_session.commit()
    db_function_session.refresh(entity)
    return entity

@pytest.fixture(scope="function")
def create_canonical_entities(db_function_session) -> List[CanonicalEntity]:
    """Create multiple test canonical entities in the database.
    
    DEPRECATED: Use CanonicalEntityFactory.create_batch() instead.
    """
    logger.warning("create_canonical_entities fixture is deprecated, use CanonicalEntityFactory.create_batch() instead")
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
        db_function_session.add(entity)
    db_function_session.commit()
    for entity in entities:
        db_function_session.refresh(entity)
    return entities

# ==================== Example Refactored Fixtures ====================
# These fixtures demonstrate how to use the new factory-based approach

@pytest.fixture(scope="function")
def test_article(db_function_session) -> Article:
    """Create a test article using the factory.
    
    This demonstrates the preferred way to create test data.
    """
    ArticleFactory._meta.sqlalchemy_session = db_function_session
    return ArticleFactory.create(
        title="Modern Test Article",
        content="This is a test article created with the factory pattern."
    )

@pytest.fixture(scope="function")
def test_entities(db_function_session, test_article) -> List[Entity]:
    """Create multiple test entities for an article using the factory.
    
    This demonstrates how to create related entities.
    """
    EntityFactory._meta.sqlalchemy_session = db_function_session
    return EntityFactory.create_batch(3, article=test_article)

@pytest.fixture(scope="function")
def test_canonical_entities_with_relationships(db_function_session) -> Dict[str, Any]:
    """Create canonical entities with relationships.
    
    This demonstrates how to create a network of related entities.
    """
    # Use the utility function from factories
    entities, relationships = create_related_entities(db_function_session, count=4)
    return {
        "entities": entities,
        "relationships": relationships
    }
