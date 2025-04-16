"""Tests for the Entity Resolver tool."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from local_newsifier.models.entity_tracking import CanonicalEntity, CanonicalEntityCreate
from local_newsifier.tools.entity_resolver import EntityResolver
from local_newsifier.database.adapter import (
    create_canonical_entity, get_canonical_entity, 
    get_canonical_entity_by_name, get_all_canonical_entities
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = Mock(spec=Session)
    return session


def test_entity_resolver_normalize_name():
    """Test normalizing entity names."""
    resolver = EntityResolver()
    
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
    resolver = EntityResolver()
    
    # Test identical names
    assert resolver.calculate_name_similarity("Joe Biden", "Joe Biden") == 1.0
    
    # Test similar names
    assert resolver.calculate_name_similarity("Joe Biden", "President Biden") > 0.5
    
    # Test different names
    assert resolver.calculate_name_similarity("Joe Biden", "Kamala Harris") < 0.5