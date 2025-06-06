"""
Configuration for services tests.
This file sets up mocks to avoid the SQLite dependency chain.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest


# Create a patch context to prevent SQLite-dependent imports when running tests
@pytest.fixture(autouse=True, scope="session")
def mock_flow_imports():
    """Mock the crewai Flow import to avoid SQLite dependency."""
    with patch.dict(
        "sys.modules",
        {
            "crewai": MagicMock(),
            "crewai.Flow": MagicMock(),
            "chromadb": MagicMock(),
        },
    ):
        yield


# Shared mock fixtures for service tests
@pytest.fixture
def mock_entity_service_deps():
    """Create standard mock dependencies for EntityService."""
    # Mock tools
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()

    # Mock CRUD operations
    mock_entity_crud = MagicMock()
    mock_canonical_entity_crud = MagicMock()
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()

    # Mock session factory
    mock_session = MagicMock()
    mock_session_factory = MagicMock(
        return_value=MagicMock(__enter__=MagicMock(return_value=mock_session), __exit__=MagicMock())
    )

    return {
        "entity_crud": mock_entity_crud,
        "canonical_entity_crud": mock_canonical_entity_crud,
        "entity_mention_context_crud": mock_entity_mention_context_crud,
        "entity_profile_crud": mock_entity_profile_crud,
        "article_crud": mock_article_crud,
        "entity_extractor": mock_entity_extractor,
        "context_analyzer": mock_context_analyzer,
        "entity_resolver": mock_entity_resolver,
        "session_factory": mock_session_factory,
        "session": mock_session,
    }


@pytest.fixture
def mock_apify_client():
    """Create a mock Apify client for testing."""
    mock_client = MagicMock()

    # Mock actor method and call
    mock_actor = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_actor.call.return_value = {"data": "test_result"}
    mock_actor.get.return_value = {"id": "test_actor", "name": "Test Actor"}

    # Mock dataset method
    mock_dataset = MagicMock()
    mock_client.dataset.return_value = mock_dataset
    mock_dataset.list_items.return_value = {"items": [{"id": 1, "name": "test"}]}

    # User info for test_connection
    mock_user = MagicMock()
    mock_client.user.return_value = mock_user
    mock_user.get.return_value = {"username": "test_user"}

    # Mock schedules for schedule operations
    mock_schedules = MagicMock()
    mock_schedules.create.return_value = {
        "id": "test_schedule_id",
        "name": "Test Schedule",
        "cronExpression": "0 0 * * *",
        "isEnabled": True,
        "actId": "test_actor_id",
    }
    mock_schedules.list.return_value = {
        "data": {
            "items": [
                {
                    "id": "test_schedule_id",
                    "name": "Test Schedule",
                    "cronExpression": "0 0 * * *",
                    "isEnabled": True,
                    "actId": "test_actor_id",
                }
            ],
            "total": 1,
        }
    }
    mock_client.schedules.return_value = mock_schedules

    # Mock individual schedule
    mock_schedule = MagicMock()
    mock_schedule.get.return_value = {
        "id": "test_schedule_id",
        "name": "Test Schedule",
        "cronExpression": "0 0 * * *",
        "isEnabled": True,
        "actId": "test_actor_id",
    }
    mock_schedule.update.return_value = {
        "id": "test_schedule_id",
        "name": "Updated Schedule",
        "cronExpression": "0 0 * * *",
        "isEnabled": True,
        "actId": "test_actor_id",
    }
    mock_schedule.delete.return_value = True
    mock_client.schedule.return_value = mock_schedule

    # Mock webhook method
    mock_webhook = MagicMock()
    mock_webhook.create.return_value = {"id": "webhook_id"}
    mock_client.webhooks.return_value = mock_webhook

    return mock_client


@pytest.fixture
def mock_pipeline_deps():
    """Create standard mock dependencies for NewsPipelineService."""
    # Mock the web scraper
    mock_web_scraper = MagicMock()
    mock_web_scraper.scrape_url.return_value = {
        "title": "Test Article",
        "content": "John Doe visited the city.",
        "published_at": datetime(2025, 1, 1),
    }

    # Mock the article service
    mock_article_service = MagicMock()
    mock_article_service.process_article.return_value = {
        "article_id": 1,
        "title": "Test Article",
        "url": "https://example.com",
        "entities": [
            {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1}
        ],
        "analysis_result": {
            "entities": [
                {"original_text": "John Doe", "canonical_name": "John Doe", "canonical_id": 1}
            ],
            "statistics": {"total_entities": 1},
        },
    }

    # Mock the file writer
    mock_file_writer = MagicMock()
    mock_file_writer.write_results.return_value = "/path/to/output.json"

    # Mock session factory
    mock_session = MagicMock()
    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__enter__.return_value = mock_session

    return {
        "web_scraper": mock_web_scraper,
        "article_service": mock_article_service,
        "file_writer": mock_file_writer,
        "session_factory": mock_session_factory,
        "session": mock_session,
    }


@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return {
        "id": 1,
        "url": "https://example.com/article-1",
        "title": "Test Article",
        "content": "This is a test article. John Doe visited Chicago yesterday.",
        "published_at": datetime(2025, 1, 1),
        "status": "analyzed",
    }


@pytest.fixture
def sample_entity():
    """Create a sample entity for testing."""
    return {
        "id": 1,
        "text": "John Doe",
        "entity_type": "PERSON",
        "canonical_entity_id": 1,
        "article_id": 1,
        "start_char": 22,
        "end_char": 30,
    }


@pytest.fixture
def sample_canonical_entity():
    """Create a sample canonical entity for testing."""
    return {
        "id": 1,
        "name": "John Doe",
        "entity_type": "PERSON",
        "first_seen": datetime(2025, 1, 1),
        "last_seen": datetime(2025, 1, 5),
        "mention_count": 10,
    }
