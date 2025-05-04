"""Tests for FastAPI endpoints using fastapi-injectable."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Annotated, Generator

from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient
from fastapi_injectable import injectable, register_app

from sqlmodel import Session


class MockInjectableEntityService:
    """Mock entity service for testing injectable endpoints."""
    
    def __init__(self):
        self.get_entity_called = False
        self.entity_id = None
    
    def get_entity(self, entity_id: int):
        """Mock method for get_entity."""
        self.get_entity_called = True
        self.entity_id = entity_id
        return {"id": entity_id, "name": f"Entity {entity_id}"}


@pytest.fixture
def mock_injectable_entity_service():
    """Provide a mock entity service."""
    return MockInjectableEntityService()


@pytest.fixture
def test_app(mock_injectable_entity_service):
    """Create a test app with injectable dependencies."""
    app = FastAPI()
    
    # Register the app with fastapi-injectable
    # Using async_to_sync to handle coroutine
    import asyncio
    
    # Create and run event loop to register app
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(register_app(app))
    
    # Define injectable provider
    @injectable
    def get_entity_service():
        return mock_injectable_entity_service
    
    # Define a test endpoint
    @app.get("/entities/{entity_id}")
    def get_entity(
        entity_id: int,
        entity_service: Annotated[MockInjectableEntityService, Depends(get_entity_service)]
    ):
        entity = entity_service.get_entity(entity_id)
        return entity
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


@pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
def test_injectable_endpoint(client, mock_injectable_entity_service):
    """Test an endpoint using injectable dependencies."""
    # Arrange
    entity_id = 123
    
    # Act
    response = client.get(f"/entities/{entity_id}")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"id": entity_id, "name": f"Entity {entity_id}"}
    assert mock_injectable_entity_service.get_entity_called
    assert mock_injectable_entity_service.entity_id == entity_id


# Test middleware and lifespan usage with fastapi-injectable adapter
@pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
def test_injectable_app_lifespan():
    """Test using the injectable app lifespan context manager."""
    # Arrange
    app = FastAPI()
    mock_register_app = MagicMock()
    mock_migrate_services = MagicMock()
    
    # Act
    @injectable
    def get_mock_service():
        return MagicMock()
    
    # Create a test route using the injectable service
    @app.get("/test")
    def test_route(service: Annotated[MagicMock, Depends(get_mock_service)]):
        return {"status": "ok"}
    
    # Assert the decorator was applied correctly
    assert hasattr(get_mock_service, "__injectable_config")
    
    # Use patch to verify lifespan setup works
    with patch("local_newsifier.fastapi_injectable_adapter.register_app", mock_register_app):
        with patch("local_newsifier.fastapi_injectable_adapter.migrate_container_services", mock_migrate_services):
            # This is only a partial test as we can't easily test the async lifespan
            # without running it, but we can verify the functions are decorated properly
            assert callable(get_mock_service)
            assert hasattr(get_mock_service, "__injectable_config")