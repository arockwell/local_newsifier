"""
Test fixtures for fastapi-injectable.

This module provides test fixtures that support testing components using 
the fastapi-injectable dependency injection system.
"""

import pytest
from unittest.mock import Mock
from typing import Dict, Generator, Optional

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from local_newsifier.di.providers import (
    get_entity_crud,
    get_canonical_entity_crud,
    get_entity_mention_context_crud,
    get_entity_profile_crud,
    get_article_crud,
    get_entity_extractor,
    get_context_analyzer,
    get_entity_resolver,
    get_session,
)


# Mock database session
@pytest.fixture
def mock_session():
    """Provide a mock database session."""
    return Mock(spec=Session)


# Mock CRUD components
@pytest.fixture
def mock_entity_crud():
    """Provide a mock entity CRUD component."""
    mock = Mock()
    mock.create.return_value = Mock(id=1, text="Test Entity", entity_type="PERSON")
    mock.get_by_article.return_value = []
    return mock


@pytest.fixture
def mock_canonical_entity_crud():
    """Provide a mock canonical entity CRUD component."""
    mock = Mock()
    mock.get_all.return_value = []
    mock.get_by_name.return_value = Mock(id=1, name="Test Entity", entity_type="PERSON")
    mock.create.return_value = Mock(id=1, name="Test Entity", entity_type="PERSON")
    return mock


@pytest.fixture
def mock_entity_mention_context_crud():
    """Provide a mock entity mention context CRUD component."""
    mock = Mock()
    mock.create.return_value = Mock(id=1)
    return mock


@pytest.fixture
def mock_entity_profile_crud():
    """Provide a mock entity profile CRUD component."""
    mock = Mock()
    return mock


@pytest.fixture
def mock_article_crud():
    """Provide a mock article CRUD component."""
    mock = Mock()
    mock.update_status.return_value = True
    mock.get_by_status.return_value = []
    return mock


# Mock tool components
@pytest.fixture
def mock_entity_extractor():
    """Provide a mock entity extractor tool."""
    mock = Mock()
    mock.extract_entities.return_value = [
        {
            "text": "Test Entity",
            "type": "PERSON",
            "context": "This is a test entity in context.",
            "confidence": 0.95
        }
    ]
    return mock


@pytest.fixture
def mock_context_analyzer():
    """Provide a mock context analyzer tool."""
    mock = Mock()
    mock.analyze_context.return_value = {
        "sentiment": {"score": 0.5, "label": "neutral"},
        "framing": {"category": "neutral", "score": 0.8}
    }
    return mock


@pytest.fixture
def mock_entity_resolver():
    """Provide a mock entity resolver tool."""
    mock = Mock()
    mock.resolve_entity.return_value = {
        "name": "Test Entity",
        "entity_type": "PERSON",
        "is_new": True
    }
    return mock


# FastAPI test client with dependency overrides
@pytest.fixture
def test_client_with_mocks(
    mock_session,
    mock_entity_crud,
    mock_canonical_entity_crud,
    mock_entity_mention_context_crud,
    mock_entity_profile_crud,
    mock_article_crud,
    mock_entity_extractor,
    mock_context_analyzer,
    mock_entity_resolver
):
    """Provide a FastAPI test client with mocked dependencies.
    
    Args:
        All mock fixture dependencies
        
    Returns:
        TestClient with dependency overrides configured
    """
    # Create a test FastAPI application
    app = FastAPI()
    
    # Configure dependency overrides
    app.dependency_overrides = {
        get_session: lambda: mock_session,
        get_entity_crud: lambda: mock_entity_crud,
        get_canonical_entity_crud: lambda: mock_canonical_entity_crud,
        get_entity_mention_context_crud: lambda: mock_entity_mention_context_crud,
        get_entity_profile_crud: lambda: mock_entity_profile_crud,
        get_article_crud: lambda: mock_article_crud,
        get_entity_extractor: lambda: mock_entity_extractor,
        get_context_analyzer: lambda: mock_context_analyzer,
        get_entity_resolver: lambda: mock_entity_resolver,
    }
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clear dependency overrides after test
    app.dependency_overrides = {}


# Patch the injectable dependencies for non-API tests
@pytest.fixture
def patch_injectable_dependencies(monkeypatch):
    """Patch injectable dependencies for non-API tests.
    
    Args:
        monkeypatch: PyTest monkeypatch fixture
        
    Returns:
        Dictionary with mock dependencies
    """
    # Create mock dependencies
    mock_entity_crud = Mock()
    mock_canonical_entity_crud = Mock()
    mock_entity_mention_context_crud = Mock()
    mock_entity_profile_crud = Mock()
    mock_article_crud = Mock()
    mock_entity_extractor = Mock()
    mock_context_analyzer = Mock()
    mock_entity_resolver = Mock()
    mock_session = Mock()
    
    # Set up common return values
    mock_entity_crud.create.return_value = Mock(id=1, text="Test Entity", entity_type="PERSON")
    mock_canonical_entity_crud.get_all.return_value = []
    mock_canonical_entity_crud.get_by_name.return_value = Mock(id=1, name="Test Entity", entity_type="PERSON")
    mock_canonical_entity_crud.create.return_value = Mock(id=1, name="Test Entity", entity_type="PERSON")
    mock_entity_extractor.extract_entities.return_value = [
        {
            "text": "Test Entity",
            "type": "PERSON",
            "context": "This is a test entity in context.",
            "confidence": 0.95
        }
    ]
    mock_context_analyzer.analyze_context.return_value = {
        "sentiment": {"score": 0.5, "label": "neutral"},
        "framing": {"category": "neutral", "score": 0.8}
    }
    mock_entity_resolver.resolve_entity.return_value = {
        "name": "Test Entity",
        "entity_type": "PERSON",
        "is_new": True
    }
    
    # Patch the providers
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_crud", lambda: mock_entity_crud)
    monkeypatch.setattr("local_newsifier.di.providers.get_canonical_entity_crud", lambda: mock_canonical_entity_crud)
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_mention_context_crud", lambda: mock_entity_mention_context_crud)
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_profile_crud", lambda: mock_entity_profile_crud)
    monkeypatch.setattr("local_newsifier.di.providers.get_article_crud", lambda: mock_article_crud)
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_extractor", lambda: mock_entity_extractor)
    monkeypatch.setattr("local_newsifier.di.providers.get_context_analyzer", lambda: mock_context_analyzer)
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_resolver", lambda: mock_entity_resolver)
    monkeypatch.setattr("local_newsifier.di.providers.get_session", lambda: mock_session)
    
    # Return mocks for use in tests
    return {
        "entity_crud": mock_entity_crud,
        "canonical_entity_crud": mock_canonical_entity_crud,
        "entity_mention_context_crud": mock_entity_mention_context_crud,
        "entity_profile_crud": mock_entity_profile_crud,
        "article_crud": mock_article_crud,
        "entity_extractor": mock_entity_extractor,
        "context_analyzer": mock_context_analyzer,
        "entity_resolver": mock_entity_resolver,
        "session": mock_session,
    }