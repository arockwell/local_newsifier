"""Tests for the Entity Resolver tool."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.entity_tracking import CanonicalEntity, CanonicalEntityCreate
from local_newsifier.tools.entity_resolver import EntityResolver


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    db_manager = Mock(spec=DatabaseManager)
    
    # Mock get_canonical_entity_by_name
    db_manager.get_canonical_entity_by_name.return_value = None
    
    # Mock create_canonical_entity
    def create_entity(entity_data):
        return CanonicalEntity(
            id=1,
            name=entity_data.name,
            entity_type=entity_data.entity_type,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
    
    db_manager.create_canonical_entity.side_effect = create_entity
    
    # Mock get_all_canonical_entities
    db_manager.get_all_canonical_entities.return_value = []
    
    return db_manager


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


def test_entity_resolver_create_new_entity(mock_db_manager):
    """Test creating a new canonical entity."""
    resolver = EntityResolver(mock_db_manager)
    
    # Test with a new entity
    entity = resolver.resolve_entity("Joe Biden", "PERSON")
    
    # Verify that the correct methods were called
    mock_db_manager.get_canonical_entity_by_name.assert_called_with("Joe Biden", "PERSON")
    mock_db_manager.create_canonical_entity.assert_called_once()
    
    # Verify the entity was created
    assert entity.name == "Joe Biden"
    assert entity.entity_type == "PERSON"


def test_entity_resolver_find_existing_entity(mock_db_manager):
    """Test finding an existing canonical entity."""
    # Mock existing entity
    existing_entity = CanonicalEntity(
        id=1,
        name="Joe Biden",
        entity_type="PERSON",
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    mock_db_manager.get_canonical_entity_by_name.return_value = existing_entity
    
    resolver = EntityResolver(mock_db_manager)
    
    # Test with an existing entity
    entity = resolver.resolve_entity("Joe Biden", "PERSON")
    
    # Verify that the correct methods were called
    mock_db_manager.get_canonical_entity_by_name.assert_called_with("Joe Biden", "PERSON")
    mock_db_manager.create_canonical_entity.assert_not_called()
    
    # Verify the entity was found
    assert entity.id == 1
    assert entity.name == "Joe Biden"
    assert entity.entity_type == "PERSON"


def test_entity_resolver_find_similar_entity(mock_db_manager):
    """Test finding a similar canonical entity."""
    # Mock similar entities
    similar_entity = CanonicalEntity(
        id=1,
        name="Joe Biden",
        entity_type="PERSON",
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc)
    )
    
    # Mock get_all_canonical_entities to return the similar entity
    mock_db_manager.get_all_canonical_entities.return_value = [similar_entity]
    
    # Use a lower threshold to match "President Biden" with "Joe Biden"
    resolver = EntityResolver(mock_db_manager, similarity_threshold=0.5)
    
    # Test with a variation of the existing entity
    entity = resolver.resolve_entity("President Biden", "PERSON")
    
    # Verify that the correct methods were called
    mock_db_manager.get_canonical_entity_by_name.assert_called()
    mock_db_manager.get_all_canonical_entities.assert_called_with("PERSON")
    
    # Verify that a new entity was not created since similarity is high
    mock_db_manager.create_canonical_entity.assert_not_called()
    
    # Verify the similar entity was found
    assert entity.id == 1
    assert entity.name == "Joe Biden"
    assert entity.entity_type == "PERSON"