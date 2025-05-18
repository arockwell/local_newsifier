import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from local_newsifier.api.routers import tasks
from local_newsifier.api.dependencies import get_article_service, get_rss_feed_service
from local_newsifier.models.article import Article


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(tasks.router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def sample_article():
    return Article(id=1, title="Sample", content="x", url="https://example.com")


def test_process_article_creates_task(client, sample_article):
    mock_service = MagicMock()
    mock_service.get_article.return_value = sample_article

    mock_task = MagicMock()
    mock_task.id = "abc123"

    with patch("local_newsifier.api.routers.tasks.process_article.delay", return_value=mock_task) as mock_delay:
        client.app.dependency_overrides[get_article_service] = lambda: mock_service
        resp = client.post("/tasks/process-article/1")
        client.app.dependency_overrides = {}

    assert resp.status_code == 200
    assert resp.json()["task_id"] == "abc123"
    mock_delay.assert_called_once_with(1)


def test_fetch_rss_feeds_creates_task(client):
    mock_service = MagicMock()
    mock_task = MagicMock()
    mock_task.id = "feed123"

    with patch("local_newsifier.api.routers.tasks.fetch_rss_feeds.delay", return_value=mock_task) as mock_delay:
        client.app.dependency_overrides[get_rss_feed_service] = lambda: mock_service
        resp = client.post("/tasks/fetch-rss-feeds", params={"feed_urls": ["a", "b"]})
        client.app.dependency_overrides = {}

    assert resp.status_code == 200
    assert resp.json()["task_id"] == "feed123"
    mock_delay.assert_called_once_with(["a", "b"])


def test_get_task_status_success(client):
    mock_result = MagicMock()
    mock_result.status = "SUCCESS"
    mock_result.successful.return_value = True
    mock_result.result = {"ok": True}

    with patch("local_newsifier.api.routers.tasks.AsyncResult", return_value=mock_result):
        resp = client.get("/tasks/status/xyz")

    assert resp.status_code == 200
    assert resp.json() == {"task_id": "xyz", "status": "SUCCESS", "result": {"ok": True}}


def test_cancel_task_running(client):
    mock_result = MagicMock()
    mock_result.successful.return_value = False
    mock_result.failed.return_value = False

    with patch("local_newsifier.api.routers.tasks.AsyncResult", return_value=mock_result), \
         patch("local_newsifier.api.routers.tasks.celery_app") as mock_celery:
        resp = client.delete("/tasks/cancel/foo")
        mock_celery.control.revoke.assert_called_once_with("foo", terminate=True)

    assert resp.status_code == 200
    assert "revoke" in resp.json()["message"]

