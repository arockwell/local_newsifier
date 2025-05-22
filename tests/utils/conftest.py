"""Common fixtures for tests using provider patching."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_session(monkeypatch):
    """Patch the get_session provider and return a mock session."""
    session = MagicMock()
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_session", lambda: session
    )
    return session


@pytest.fixture
def mock_rss_feed_service(monkeypatch):
    """Patch the RSS feed service provider."""
    service = MagicMock()
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_rss_feed_service", lambda: service
    )
    return service


@pytest.fixture
def mock_article_crud(monkeypatch):
    """Patch the article CRUD provider."""
    crud = MagicMock()
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_article_crud", lambda: crud
    )
    return crud


@pytest.fixture
def mock_flows(monkeypatch):
    """Patch flow providers and return mocks."""
    news_flow = MagicMock()
    entity_flow = MagicMock()
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_news_pipeline_flow", lambda: news_flow
    )
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_entity_tracking_flow", lambda: entity_flow
    )
    return {"news_pipeline_flow": news_flow, "entity_tracking_flow": entity_flow}
