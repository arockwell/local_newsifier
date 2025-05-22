"""Example test for an injectable service using the simplified testing approach."""

import pytest
from unittest.mock import MagicMock
from typing import Annotated, Dict, List, Optional
from unittest.mock import patch, MagicMock

from fastapi import Depends

# Create a mock injectable decorator for testing
mock_injectable = MagicMock()


def mock_decorator(use_cache=True):
    def wrapper(func):
        func.__injectable_config = True
        return func

    return wrapper


mock_injectable.side_effect = mock_decorator

# Patch the real injectable with our mock
with patch("fastapi_injectable.injectable", mock_injectable):
    from fastapi_injectable import injectable
from sqlmodel import Session

# Import testing utilities
from tests.conftest_injectable import (
    mock_injectable_dependencies,
    create_mock_service,
)


# Define a simple injectable service for demonstration purposes
@injectable(use_cache=False)
class ExampleEntityService:
    """Example injectable entity service for testing purposes."""

    def __init__(
        self,
        entity_crud: Annotated[object, Depends("get_entity_crud")],
        canonical_entity_crud: Annotated[object, Depends("get_canonical_entity_crud")],
        session: Annotated[Session, Depends("get_session")],
    ):
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.session = session

    def get_entity(self, entity_id: int) -> Dict:
        """Get an entity by ID."""
        return self.entity_crud.get(self.session, id=entity_id)

    def get_entities_by_type(self, entity_type: str) -> List[Dict]:
        """Get entities by type."""
        return self.entity_crud.get_by_type(self.session, entity_type=entity_type)

    def create_entity(self, entity_data: Dict) -> Dict:
        """Create a new entity."""
        # Check if entity already exists
        if existing := self.entity_crud.get_by_name(self.session, name=entity_data.get("name")):
            return existing

        # Create new entity
        return self.entity_crud.create(self.session, obj_in=entity_data)

    def resolve_to_canonical(self, entity_id: int) -> Dict:
        """Resolve an entity to its canonical representation."""
        # Get the entity
        entity = self.entity_crud.get(self.session, id=entity_id)
        if not entity:
            return None

        # Find or create canonical entity
        canonical = self.canonical_entity_crud.get_by_name(self.session, name=entity.get("name"))

        if not canonical:
            # Create new canonical entity
            canonical_data = {
                "name": entity.get("name"),
                "entity_type": entity.get("entity_type"),
                "description": f"Canonical entity for {entity.get('name')}",
            }
            canonical = self.canonical_entity_crud.create(self.session, obj_in=canonical_data)

        return canonical


class TestExampleEntityService:
    """Tests for the ExampleEntityService."""

    def test_get_entity(self, mock_injectable_dependencies):
        """Test getting an entity by ID."""
        # Arrange - create mocks
        entity_crud_mock = MagicMock()
        entity_data = {"id": 1, "name": "Test Entity", "entity_type": "PERSON"}
        entity_crud_mock.get.return_value = entity_data

        session_mock = MagicMock()

        # Create service with mocks
        service = ExampleEntityService(
            entity_crud=entity_crud_mock,
            canonical_entity_crud=MagicMock(),
            session=session_mock,
        )

        # Act
        result = service.get_entity(1)

        # Assert
        assert result == entity_data
        entity_crud_mock.get.assert_called_once_with(session_mock, id=1)

    def test_get_entities_by_type(self, mock_injectable_dependencies):
        """Test getting entities by type."""
        # Arrange - create and register mocks
        mock = mock_injectable_dependencies

        entity_crud_mock = MagicMock()
        entity_type = "PERSON"
        entities = [
            {"id": 1, "name": "Person 1", "entity_type": entity_type},
            {"id": 2, "name": "Person 2", "entity_type": entity_type},
        ]
        entity_crud_mock.get_by_type.return_value = entities

        session_mock = MagicMock()

        # Register mocks
        mock.register("get_entity_crud", entity_crud_mock)
        mock.register("get_canonical_entity_crud", MagicMock())
        mock.register("get_session", session_mock)

        # Create service with registered mocks
        service = ExampleEntityService(
            entity_crud=mock.get("get_entity_crud"),
            canonical_entity_crud=mock.get("get_canonical_entity_crud"),
            session=mock.get("get_session"),
        )

        # Act
        result = service.get_entities_by_type(entity_type)

        # Assert
        assert result == entities
        entity_crud_mock.get_by_type.assert_called_once_with(session_mock, entity_type=entity_type)

    def test_create_entity_new(self, mock_injectable_dependencies):
        """Test creating a new entity."""
        # Arrange - using helper function and registered mocks
        entity_crud_mock = MagicMock()
        entity_crud_mock.get_by_name.return_value = None  # Entity doesn't exist

        entity_data = {"name": "New Entity", "entity_type": "ORG"}
        created_entity = {**entity_data, "id": 1}
        entity_crud_mock.create.return_value = created_entity

        # Create service with direct mock injection
        service = create_mock_service(
            ExampleEntityService,
            entity_crud=entity_crud_mock,
            canonical_entity_crud=MagicMock(),
            session=MagicMock(),
        )

        # Act
        result = service.create_entity(entity_data)

        # Assert
        assert result == created_entity
        entity_crud_mock.get_by_name.assert_called_once()
        entity_crud_mock.create.assert_called_once()

    def test_create_entity_existing(self, mock_injectable_dependencies):
        """Test creating an entity that already exists."""
        # Arrange
        entity_crud_mock = MagicMock()
        existing_entity = {"id": 1, "name": "Existing Entity", "entity_type": "ORG"}
        entity_crud_mock.get_by_name.return_value = existing_entity

        # Register mocks
        mock = mock_injectable_dependencies
        mock.register("get_entity_crud", entity_crud_mock)
        mock.register("get_canonical_entity_crud", MagicMock())
        mock.register("get_session", MagicMock())

        # Create service using registered mocks
        service = ExampleEntityService(
            entity_crud=mock.get("get_entity_crud"),
            canonical_entity_crud=mock.get("get_canonical_entity_crud"),
            session=mock.get("get_session"),
        )

        # Act
        result = service.create_entity({"name": "Existing Entity"})

        # Assert
        assert result == existing_entity
        entity_crud_mock.get_by_name.assert_called_once()
        entity_crud_mock.create.assert_not_called()

    def test_resolve_to_canonical_existing(self, mock_injectable_dependencies):
        """Test resolving an entity to an existing canonical entity."""
        # Arrange
        entity_crud_mock = MagicMock()
        entity = {"id": 1, "name": "Test Entity", "entity_type": "PERSON"}
        entity_crud_mock.get.return_value = entity

        canonical_entity_crud_mock = MagicMock()
        canonical_entity = {
            "id": 101,
            "name": "Test Entity",
            "entity_type": "PERSON",
            "description": "Existing canonical entity",
        }
        canonical_entity_crud_mock.get_by_name.return_value = canonical_entity

        # Create service
        service = create_mock_service(
            ExampleEntityService,
            entity_crud=entity_crud_mock,
            canonical_entity_crud=canonical_entity_crud_mock,
            session=MagicMock(),
        )

        # Act
        result = service.resolve_to_canonical(1)

        # Assert
        assert result == canonical_entity
        entity_crud_mock.get.assert_called_once()
        canonical_entity_crud_mock.get_by_name.assert_called_once()
        canonical_entity_crud_mock.create.assert_not_called()

    def test_resolve_to_canonical_new(self, mock_injectable_dependencies):
        """Test resolving an entity to a new canonical entity."""
        # Arrange
        entity_crud_mock = MagicMock()
        entity = {"id": 1, "name": "New Entity", "entity_type": "PERSON"}
        entity_crud_mock.get.return_value = entity

        canonical_entity_crud_mock = MagicMock()
        canonical_entity_crud_mock.get_by_name.return_value = None  # No existing canonical

        new_canonical = {
            "id": 201,
            "name": "New Entity",
            "entity_type": "PERSON",
            "description": "Canonical entity for New Entity",
        }
        canonical_entity_crud_mock.create.return_value = new_canonical

        session_mock = MagicMock()

        # Create service
        service = ExampleEntityService(
            entity_crud=entity_crud_mock,
            canonical_entity_crud=canonical_entity_crud_mock,
            session=session_mock,
        )

        # Act
        result = service.resolve_to_canonical(1)

        # Assert
        assert result == new_canonical
        entity_crud_mock.get.assert_called_once_with(session_mock, id=1)
        canonical_entity_crud_mock.get_by_name.assert_called_once()
        canonical_entity_crud_mock.create.assert_called_once()
