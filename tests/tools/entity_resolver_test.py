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
    
    # Store created entities
    created_entities = {}
    
    # Mock session
    db_manager.session = Mock()
    
    # Mock exec for session
    mock_exec = Mock()
    db_manager.session.exec.return_value = mock_exec
    
    # Mock first and all
    mock_exec.first.return_value = None
    mock_exec.all.return_value = []
    
    # Set up for both legacy and SQLModel patterns
    
    # Mock create_canonical_entity method
    def create_entity(entity_data):
        entity = CanonicalEntity(
            id=len(created_entities) + 1,
            name=entity_data.name if hasattr(entity_data, 'name') else entity_data['name'],
            entity_type=entity_data.entity_type if hasattr(entity_data, 'entity_type') else entity_data['entity_type'],
            description=entity_data.description if hasattr(entity_data, 'description') else entity_data.get('description'),
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
        created_entities[entity.id] = entity
        return entity
    
    db_manager.create_canonical_entity.side_effect = create_entity
    
    # Mock session.add and session.commit pattern
    def session_add(entity):
        if hasattr(entity, 'id') and entity.id is None:
            entity.id = len(created_entities) + 1
        if hasattr(entity, 'id'):
            created_entities[entity.id] = entity
    
    db_manager.session.add.side_effect = session_add
    
    # Mock refresh to simulate database assignment of ID
    def session_refresh(entity):
        if not hasattr(entity, 'id') or entity.id is None:
            entity.id = len(created_entities) + 1
            created_entities[entity.id] = entity
    
    db_manager.session.refresh.side_effect = session_refresh
    
    # Mock get_canonical_entity method
    def get_entity(entity_id):
        return created_entities.get(entity_id)
    
    db_manager.get_canonical_entity.side_effect = get_entity
    
    # Mock get_canonical_entity_by_name method
    def get_entity_by_name(name, entity_type):
        for entity in created_entities.values():
            if entity.name == name and entity.entity_type == entity_type:
                return entity
        return None
    
    db_manager.get_canonical_entity_by_name.side_effect = get_entity_by_name
    
    # Mock SQLModel pattern for select and where
    def mock_select_where_for_name(*args, **kwargs):
        # Simulate the select().where() chain
        mock_where = Mock()
        mock_exec_result = Mock()
        
        # Look for the name and entity_type in the args/kwargs
        # This is a simplification - in a real test you'd parse the conditions
        mock_exec_result.first.side_effect = get_entity_by_name
        
        mock_where.exec.return_value = mock_exec_result
        return mock_where
    
    # Mock exec to return all entities for a given type
    def mock_exec_all_entities():
        mock_result = Mock()
        
        def all_for_type(*args, **kwargs):
            # This is called when we do session.exec(statement).all()
            entity_type = kwargs.get('entity_type')
            return get_all_entities(entity_type)
            
        mock_result.all.side_effect = all_for_type
        return mock_result
    
    db_manager.session.exec.return_value.all.side_effect = lambda: list(created_entities.values())
    
    # Mock get_all_canonical_entities method
    def get_all_entities(entity_type=None):
        entities = list(created_entities.values())
        if entity_type:
            entities = [e for e in entities if e.entity_type == entity_type]
        return entities
    
    db_manager.get_all_canonical_entities.side_effect = get_all_entities
    
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
    # Create an existing entity first
    entity_data = CanonicalEntityCreate(
        name="Joe Biden",
        entity_type="PERSON",
        description=None
    )
    existing_entity = mock_db_manager.create_canonical_entity(entity_data)
    
    # Reset the mock call counts
    mock_db_manager.create_canonical_entity.reset_mock()
    
    resolver = EntityResolver(mock_db_manager)
    
    # Test with an existing entity
    entity = resolver.resolve_entity("Joe Biden", "PERSON")
    
    # Verify that the correct methods were called
    mock_db_manager.get_canonical_entity_by_name.assert_called_with("Joe Biden", "PERSON")
    mock_db_manager.create_canonical_entity.assert_not_called()
    assert entity == existing_entity


def test_entity_resolver_find_similar_entity(mock_db_manager):
    """Test finding a similar canonical entity."""
    # Create a similar entity first
    entity_data = CanonicalEntityCreate(
        name="Joe Biden",
        entity_type="PERSON",
        description=None
    )
    similar_entity = mock_db_manager.create_canonical_entity(entity_data)
    
    # Reset the mock call counts
    mock_db_manager.create_canonical_entity.reset_mock()
    
    # Use a lower threshold to match "President Biden" with "Joe Biden"
    resolver = EntityResolver(mock_db_manager, similarity_threshold=0.5)
    
    # Test with a variation of the existing entity
    entity = resolver.resolve_entity("President Biden", "PERSON")
    
    # Verify that the correct methods were called
    mock_db_manager.get_canonical_entity_by_name.assert_called()
    mock_db_manager.get_all_canonical_entities.assert_called_with("PERSON")
    mock_db_manager.create_canonical_entity.assert_not_called()
    assert entity == similar_entity


def test_create_canonical_entity(mock_db_manager):
    """Test creating a canonical entity."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Joe Biden",
        entity_type="PERSON",
        description="46th President of the United States"
    )
    
    canonical_entity = mock_db_manager.create_canonical_entity(entity_data)
    
    # Verify entity was created
    assert canonical_entity.id is not None
    assert canonical_entity.name == "Joe Biden"
    assert canonical_entity.entity_type == "PERSON"
    assert canonical_entity.description == "46th President of the United States"
    assert canonical_entity.first_seen is not None
    assert canonical_entity.last_seen is not None


def test_get_canonical_entity(mock_db_manager):
    """Test getting a canonical entity by ID."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Kamala Harris",
        entity_type="PERSON",
        description="Vice President of the United States"
    )
    
    created_entity = mock_db_manager.create_canonical_entity(entity_data)
    
    # Get canonical entity
    retrieved_entity = mock_db_manager.get_canonical_entity(created_entity.id)
    
    # Verify entity was retrieved
    assert retrieved_entity is not None
    assert retrieved_entity.id == created_entity.id
    assert retrieved_entity.name == "Kamala Harris"
    assert retrieved_entity.entity_type == "PERSON"
    assert retrieved_entity.description == "Vice President of the United States"


def test_get_canonical_entity_by_name(mock_db_manager):
    """Test getting a canonical entity by name and type."""
    # Create canonical entity
    entity_data = CanonicalEntityCreate(
        name="Barack Obama",
        entity_type="PERSON",
        description="44th President of the United States"
    )
    
    mock_db_manager.create_canonical_entity(entity_data)
    
    # Get canonical entity by name
    retrieved_entity = mock_db_manager.get_canonical_entity_by_name("Barack Obama", "PERSON")
    
    # Verify entity was retrieved
    assert retrieved_entity is not None
    assert retrieved_entity.name == "Barack Obama"
    assert retrieved_entity.entity_type == "PERSON"
    assert retrieved_entity.description == "44th President of the United States"