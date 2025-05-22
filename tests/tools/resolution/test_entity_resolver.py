"""Tests for the EntityResolver tool."""

import os

import pytest

from local_newsifier.tools.resolution.entity_resolver import EntityResolver
from tests.fixtures.event_loop import event_loop_fixture

pytestmark = pytest.mark.usefixtures("event_loop_fixture")


@pytest.fixture
def entity_resolver():
    """Create an EntityResolver instance for testing.

    This creates the resolver directly without dependency injection
    to maintain backward compatibility in tests.
    """
    return EntityResolver(similarity_threshold=0.85)


def test_normalize_entity_name(entity_resolver):
    """Test normalizing entity names."""
    # Test with title
    assert entity_resolver.normalize_entity_name("President Joe Biden") == "Joe Biden"
    
    # Test with reversed name
    assert entity_resolver.normalize_entity_name("Biden, Joe") == "Joe Biden"
    
    # Test with middle initial
    assert entity_resolver.normalize_entity_name("Joe R. Biden") == "Joe Biden"
    
    # Test with suffix
    assert entity_resolver.normalize_entity_name("Joe Biden Jr.") == "Joe Biden"
    
    # Test with no patterns
    assert entity_resolver.normalize_entity_name("Joe Biden") == "Joe Biden"


def test_calculate_name_similarity(entity_resolver):
    """Test calculating similarity between entity names."""
    # Test exact match
    assert entity_resolver.calculate_name_similarity("Joe Biden", "Joe Biden") == 1.0
    
    # Test case difference
    assert entity_resolver.calculate_name_similarity("Joe Biden", "joe biden") == 1.0
    
    # Test with title
    assert entity_resolver.calculate_name_similarity("President Joe Biden", "Joe Biden") > 0.85
    
    # Test with middle initial
    assert entity_resolver.calculate_name_similarity("Joe R. Biden", "Joe Biden") > 0.85
    
    # Test with different names
    assert entity_resolver.calculate_name_similarity("Joe Biden", "Donald Trump") < 0.5


def test_find_matching_entity(entity_resolver):
    """Test finding matching entity from existing entities."""
    # Create test entities
    existing_entities = [
        {"name": "Joe Biden", "entity_type": "PERSON"},
        {"name": "Donald Trump", "entity_type": "PERSON"},
        {"name": "Apple Inc.", "entity_type": "ORG"},
        {"name": "San Francisco", "entity_type": "GPE"}
    ]
    
    # Test exact match
    match = entity_resolver.find_matching_entity("Joe Biden", "PERSON", existing_entities)
    assert match is not None
    assert match["name"] == "Joe Biden"
    
    # Test case difference
    match = entity_resolver.find_matching_entity("joe biden", "PERSON", existing_entities)
    assert match is not None
    assert match["name"] == "Joe Biden"
    
    # Test with title
    match = entity_resolver.find_matching_entity("President Joe Biden", "PERSON", existing_entities)
    assert match is not None
    assert match["name"] == "Joe Biden"
    
    # Test with different entity type
    match = entity_resolver.find_matching_entity("Joe Biden", "ORG", existing_entities)
    assert match is None
    
    # Test with non-existent entity
    match = entity_resolver.find_matching_entity("Barack Obama", "PERSON", existing_entities)
    assert match is None


def test_resolve_entity_new(entity_resolver):
    """Test resolving a new entity."""
    # Resolve entity with no existing entities
    result = entity_resolver.resolve_entity("Joe Biden", "PERSON")
    
    # Verify result
    assert result["name"] == "Joe Biden"
    assert result["entity_type"] == "PERSON"
    assert result["is_new"] is True
    assert result["confidence"] == 1.0
    assert result["original_text"] == "Joe Biden"


def test_resolve_entity_existing(entity_resolver):
    """Test resolving an entity that matches an existing entity."""
    # Create test entities
    existing_entities = [
        {"name": "Joe Biden", "entity_type": "PERSON"},
        {"name": "Donald Trump", "entity_type": "PERSON"}
    ]
    
    # Resolve entity with existing entities
    result = entity_resolver.resolve_entity("President Joe Biden", "PERSON", existing_entities)
    
    # Verify result
    assert result["name"] == "Joe Biden"
    assert result["entity_type"] == "PERSON"
    assert result["is_new"] is False
    assert result["confidence"] > 0.85
    assert result["original_text"] == "President Joe Biden"


def test_resolve_entity_no_match(entity_resolver):
    """Test resolving an entity that doesn't match any existing entity."""
    # Create test entities
    existing_entities = [
        {"name": "Joe Biden", "entity_type": "PERSON"},
        {"name": "Donald Trump", "entity_type": "PERSON"}
    ]
    
    # Resolve entity with existing entities
    result = entity_resolver.resolve_entity("Barack Obama", "PERSON", existing_entities)
    
    # Verify result
    assert result["name"] == "Barack Obama"
    assert result["entity_type"] == "PERSON"
    assert result["is_new"] is True
    assert result["confidence"] == 1.0
    assert result["original_text"] == "Barack Obama"


def test_resolve_entities(entity_resolver):
    """Test resolving multiple entities."""
    # Create test entities
    entities = [
        {"text": "Joe Biden", "type": "PERSON"},
        {"text": "President Donald Trump", "type": "PERSON"},
        {"text": "Barack Obama", "type": "PERSON"},
        {"text": "Apple Inc.", "type": "ORG"}
    ]
    
    # Create existing canonical entities
    existing_entities = [
        {"name": "Joe Biden", "entity_type": "PERSON"},
        {"name": "Donald Trump", "entity_type": "PERSON"}
    ]
    
    # Resolve entities
    results = entity_resolver.resolve_entities(entities, existing_entities)
    
    # Verify results
    assert len(results) == 4
    
    # Check that each entity has a canonical field
    for entity in results:
        assert "canonical" in entity
        assert "name" in entity["canonical"]
        assert "entity_type" in entity["canonical"]
        assert "is_new" in entity["canonical"]
        
    # Check specific entities
    assert results[0]["canonical"]["name"] == "Joe Biden"
    assert results[0]["canonical"]["is_new"] is False
    
    assert results[1]["canonical"]["name"] == "Donald Trump"
    assert results[1]["canonical"]["is_new"] is False
    
    assert results[2]["canonical"]["name"] == "Barack Obama"
    assert results[2]["canonical"]["is_new"] is True
    
    assert results[3]["canonical"]["name"] == "Apple Inc."
    assert results[3]["canonical"]["is_new"] is True


def test_resolve_entities_empty(entity_resolver):
    """Test resolving an empty list of entities."""
    # Resolve empty list
    results = entity_resolver.resolve_entities([])
    
    # Verify results
    assert results == []


def test_resolve_entities_missing_fields(entity_resolver):
    """Test resolving entities with missing fields."""
    # Create test entities with missing fields
    entities = [
        {"text": "Joe Biden", "type": "PERSON"},
        {"text": "Donald Trump"},  # Missing type
        {"type": "PERSON"},  # Missing text
        {}  # Missing both
    ]
    
    # Resolve entities
    results = entity_resolver.resolve_entities(entities)
    
    # Verify results - only the first entity should be processed
    assert len(results) == 1
    assert results[0]["text"] == "Joe Biden"
