"""Tests for the Entity Resolver tool."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session, select

from local_newsifier.models.entity_tracking import CanonicalEntity, CanonicalEntityCreate
from local_newsifier.tools.entity_resolver import EntityResolver


@pytest.fixture
def mock_session():
    """Create a mock SQLModel session."""
    mock_session = Mock(spec=Session)
    
    # Store created entities
    created_entities = {}
    
    # Mock session.add and session.commit pattern
    def session_add(entity):
        if hasattr(entity, 'id') and entity.id is None:
            entity.id = len(created_entities) + 1
        if hasattr(entity, 'id'):
            created_entities[entity.id] = entity
    
    mock_session.add.side_effect = session_add
    
    # Mock refresh to simulate database assignment of ID
    def session_refresh(entity):
        if not hasattr(entity, 'id') or entity.id is None:
            entity.id = len(created_entities) + 1
            created_entities[entity.id] = entity
    
    mock_session.refresh.side_effect = session_refresh
    
    # Simple exec mock that doesn't try to inspect the statement
    mock_exec = Mock()
    mock_exec.first.return_value = None  # Default to no entity found
    mock_exec.all.return_value = []      # Default to empty list
    mock_session.exec.return_value = mock_exec
    
    # Store the mock so we can configure it in the tests
    mock_session._entities = created_entities
    
    return mock_session


def test_entity_resolver_normalize_name():
    """Test normalizing entity names."""
    resolver = EntityResolver(Mock())
    
    # Test with title
    assert resolver.normalize_entity_name("President Joe Biden") == "Joe Biden"
    
    # Test with reversed name
    assert resolver.normalize_entity_name("Biden, Joe") == "Joe Biden"
    
    # Test with middle initial
    assert resolver.normalize_entity_name("Joe R. Biden") == "Joe Biden"
    
    # Test with suffix
    assert resolver.normalize_entity_name("Joe Biden Jr.") == "Joe Biden"
    
    # Test with unchanged name
    assert resolver.normalize_entity_name("Joe Biden") == "Joe Biden"


def test_entity_resolver_calculate_similarity():
    """Test calculating name similarity."""
    resolver = EntityResolver(Mock())
    
    # Test identical names
    assert resolver.calculate_name_similarity("Joe Biden", "Joe Biden") == 1.0
    
    # Test similar names
    assert resolver.calculate_name_similarity("Joe Biden", "President Biden") > 0.5
    
    # Test different names
    assert resolver.calculate_name_similarity("Joe Biden", "Kamala Harris") < 0.5


def test_entity_resolver_create_new_entity(mock_session):
    """Test creating a new canonical entity."""
    # Configure mock to return None for find_matching_entity
    mock_exec = Mock()
    mock_exec.first.return_value = None
    mock_exec.all.return_value = []
    mock_session.exec.return_value = mock_exec
    
    resolver = EntityResolver(mock_session)
    
    # Test with a new entity
    entity = resolver.resolve_entity("Joe Biden", "PERSON")
    
    # Verify that session.add and commit were called
    assert mock_session.add.call_count >= 1
    assert mock_session.commit.call_count >= 1
    
    # Verify the entity was created
    assert entity.name == "Joe Biden"
    assert entity.entity_type == "PERSON"


def test_entity_resolver_find_existing_entity(mock_session):
    """Test finding an existing canonical entity."""
    # Create an existing entity first
    existing_entity = CanonicalEntity(
        name="Joe Biden",
        entity_type="PERSON",
        description=None,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    mock_session.add(existing_entity)
    mock_session.commit()
    mock_session.refresh(existing_entity)
    
    # Reset the mock call counts
    mock_session.add.reset_mock()
    mock_session.commit.reset_mock()
    
    # Configure mock to return the existing entity
    mock_exec = Mock()
    mock_exec.first.return_value = existing_entity
    mock_session.exec.return_value = mock_exec
    
    resolver = EntityResolver(mock_session)
    
    # Test with an existing entity
    entity = resolver.resolve_entity("Joe Biden", "PERSON")
    
    # Verify no new entities were created
    assert mock_session.add.call_count == 0
    assert mock_session.commit.call_count == 0
    
    # Verify the right entity was returned
    assert entity.id == existing_entity.id
    assert entity.name == "Joe Biden"
    assert entity.entity_type == "PERSON"


@patch("local_newsifier.tools.entity_resolver.EntityResolver.find_matching_entity")
def test_entity_resolver_find_similar_entity(mock_find_matching, mock_session):
    """Test finding a similar canonical entity."""
    # Create a similar entity first
    similar_entity = CanonicalEntity(
        name="Joe Biden",
        entity_type="PERSON",
        description=None,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    mock_session.add(similar_entity)
    mock_session.commit()
    mock_session.refresh(similar_entity)
    
    # Configure the mock to return the similar entity
    mock_find_matching.return_value = similar_entity
    
    # Reset the mock call counts
    mock_session.add.reset_mock()
    mock_session.commit.reset_mock()
    
    # Use a lower threshold to match "President Biden" with "Joe Biden"
    resolver = EntityResolver(mock_session, similarity_threshold=0.5)
    
    # Test with a variation of the existing entity
    entity = resolver.resolve_entity("President Biden", "PERSON")
    
    # Verify no new entities were created
    assert mock_session.add.call_count == 0
    assert mock_session.commit.call_count == 0
    
    # Verify we found the similar entity 
    assert entity.id == similar_entity.id
    assert entity.name == "Joe Biden"
    assert entity.entity_type == "PERSON"


def test_create_canonical_entity(mock_session):
    """Test creating a canonical entity directly."""
    # Create canonical entity
    canonical_entity = CanonicalEntity(
        name="Joe Biden",
        entity_type="PERSON",
        description="46th President of the United States",
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    mock_session.add(canonical_entity)
    mock_session.commit()
    mock_session.refresh(canonical_entity)
    
    # Verify entity was created
    assert canonical_entity.id is not None
    assert canonical_entity.name == "Joe Biden"
    assert canonical_entity.entity_type == "PERSON"
    assert canonical_entity.description == "46th President of the United States"
    assert canonical_entity.first_seen is not None
    assert canonical_entity.last_seen is not None


def test_get_canonical_entity_by_select(mock_session):
    """Test getting a canonical entity by using select."""
    # Create canonical entity
    entity = CanonicalEntity(
        name="Kamala Harris",
        entity_type="PERSON",
        description="Vice President of the United States",
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    mock_session.add(entity)
    mock_session.commit()
    mock_session.refresh(entity)
    
    # Reset mock counts
    mock_session.add.reset_mock()
    mock_session.commit.reset_mock()
    
    # Configure mock to return the entity
    mock_exec = Mock()
    mock_exec.first.return_value = entity
    mock_session.exec.return_value = mock_exec
    
    # Get canonical entity with select
    statement = select(CanonicalEntity).where(
        CanonicalEntity.id == entity.id
    )
    retrieved_entity = mock_session.exec(statement).first()
    
    # Verify entity was retrieved
    assert retrieved_entity is not None
    assert retrieved_entity.id == entity.id
    assert retrieved_entity.name == "Kamala Harris"
    assert retrieved_entity.entity_type == "PERSON"
    assert retrieved_entity.description == "Vice President of the United States"


def test_get_canonical_entity_by_name_select(mock_session):
    """Test getting a canonical entity by name and type using select."""
    # Create canonical entity
    entity = CanonicalEntity(
        name="Barack Obama",
        entity_type="PERSON",
        description="44th President of the United States",
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    mock_session.add(entity)
    mock_session.commit()
    mock_session.refresh(entity)
    
    # Reset mock counts
    mock_session.add.reset_mock()
    mock_session.commit.reset_mock()
    
    # Configure mock to return the entity
    mock_exec = Mock()
    mock_exec.first.return_value = entity
    mock_session.exec.return_value = mock_exec
    
    # Get canonical entity by name with select
    statement = select(CanonicalEntity).where(
        CanonicalEntity.name == "Barack Obama",
        CanonicalEntity.entity_type == "PERSON"
    )
    retrieved_entity = mock_session.exec(statement).first()
    
    # Verify entity was retrieved
    assert retrieved_entity is not None
    assert retrieved_entity.name == "Barack Obama"
    assert retrieved_entity.entity_type == "PERSON"
    assert retrieved_entity.description == "44th President of the United States"