"""Tests for the EntityExtractor tool."""

import pytest
from local_newsifier.tools.extraction.entity_extractor import EntityExtractor


@pytest.fixture
def entity_extractor():
    """Create an EntityExtractor instance for testing."""
    return EntityExtractor()


def test_extract_entities(entity_extractor):
    """Test extracting entities from text."""
    # Sample text with multiple entity types
    text = "John Smith works at Apple Inc. in San Francisco."
    
    # Extract all entities
    entities = entity_extractor.extract_entities(text)
    
    # Verify entities were extracted
    assert len(entities) >= 3
    
    # Check entity types
    entity_types = {entity["type"] for entity in entities}
    assert "PERSON" in entity_types
    assert "ORG" in entity_types
    assert "GPE" in entity_types  # Geo-political entity (city)
    
    # Check entity text
    entity_texts = {entity["text"] for entity in entities}
    assert "John Smith" in entity_texts
    assert "Apple Inc." in entity_texts
    assert "San Francisco" in entity_texts
    
    # Check that each entity has context
    for entity in entities:
        assert "context" in entity
        assert entity["context"]  # Context should not be empty


def test_extract_person_entities(entity_extractor):
    """Test extracting only person entities."""
    # Sample text with multiple entity types
    text = "John Smith and Mary Johnson work at Apple Inc. in San Francisco."
    
    # Extract only person entities
    entities = entity_extractor.extract_person_entities(text)
    
    # Verify only person entities were extracted
    assert len(entities) >= 2
    assert all(entity["type"] == "PERSON" for entity in entities)
    
    # Check entity text
    entity_texts = {entity["text"] for entity in entities}
    assert "John Smith" in entity_texts
    assert "Mary Johnson" in entity_texts
    assert "Apple Inc." not in entity_texts
    assert "San Francisco" not in entity_texts


def test_extract_organization_entities(entity_extractor):
    """Test extracting only organization entities."""
    # Sample text with multiple entity types
    text = "John Smith works at Apple Inc. and Microsoft Corp. in San Francisco."
    
    # Extract only organization entities
    entities = entity_extractor.extract_organization_entities(text)
    
    # Verify only organization entities were extracted
    assert len(entities) >= 2
    assert all(entity["type"] == "ORG" for entity in entities)
    
    # Check entity text
    entity_texts = {entity["text"] for entity in entities}
    assert "Apple Inc." in entity_texts
    assert "Microsoft Corp." in entity_texts
    assert "John Smith" not in entity_texts
    assert "San Francisco" not in entity_texts


def test_extract_location_entities(entity_extractor):
    """Test extracting only location entities."""
    # Sample text with multiple entity types
    text = "John Smith works in San Francisco and travels to New York."
    
    # Extract only location entities
    entities = entity_extractor.extract_location_entities(text)
    
    # Verify only location entities were extracted
    assert len(entities) >= 2
    assert all(entity["type"] in ["GPE", "LOC"] for entity in entities)
    
    # Check entity text
    entity_texts = {entity["text"] for entity in entities}
    assert "San Francisco" in entity_texts
    assert "New York" in entity_texts
    assert "John Smith" not in entity_texts


def test_extract_entities_with_context(entity_extractor):
    """Test extracting entities with expanded context."""
    # Sample text with multiple sentences
    text = """
    John Smith is the CEO of Acme Corp. He has been with the company for 10 years.
    Acme Corp. is based in San Francisco. The company has offices in New York as well.
    """
    
    # Extract entities with expanded context
    entities = entity_extractor.extract_entities_with_context(text, context_window=1)
    
    # Verify entities were extracted
    assert len(entities) >= 4
    
    # Check that each entity has expanded context
    for entity in entities:
        assert "expanded_context" in entity
        assert entity["expanded_context"]  # Expanded context should not be empty
        
        # Expanded context should be longer than or equal to the original context
        assert len(entity["expanded_context"]) >= len(entity["context"])
        
        # Entity text should be in the expanded context
        assert entity["text"] in entity["expanded_context"]


def test_empty_text(entity_extractor):
    """Test behavior with empty text."""
    # Extract entities from empty text
    entities = entity_extractor.extract_entities("")
    
    # Should return empty list, not error
    assert entities == []


def test_text_without_entities(entity_extractor):
    """Test behavior with text that has no entities."""
    # Text without any named entities
    text = "The sky is blue and the grass is green."
    
    # Extract entities
    entities = entity_extractor.extract_entities(text)
    
    # Should return empty list
    assert entities == []
