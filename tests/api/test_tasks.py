"""Tests for task API endpoints."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

from local_newsifier.api.routers import tasks as tasks_router
from local_newsifier.api.routers.tasks import router


@pytest.fixture(autouse=True)
def clear_store():
    tasks_router.TASK_STORE.clear()
    yield
    tasks_router.TASK_STORE.clear()


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_tasks_dashboard(client):
    with patch("local_newsifier.api.routers.tasks.get_templates") as gt:
        tmpl = gt.return_value
        tmpl.TemplateResponse.return_value = "ok"
        resp = client.get("/tasks/dashboard")
        assert resp.status_code == 200
        tmpl.TemplateResponse.assert_called_once()


def test_create_and_get_task(client):
    with patch("local_newsifier.api.routers.tasks._run_process_article") as run:
        resp = client.post("/tasks/process_article", params={"article_id": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "process_article"
        task_id = data["id"]
        run.assert_called_once()

    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == task_id


def test_list_tasks_filter(client):
    tasks_router.TASK_STORE["a"] = tasks_router.TaskRecord(
        id="a", name="t1", status="queued", created_at=tasks_router.datetime.now(tasks_router.timezone.utc)
    )
    tasks_router.TASK_STORE["b"] = tasks_router.TaskRecord(
        id="b", name="t2", status="completed", created_at=tasks_router.datetime.now(tasks_router.timezone.utc)
    )

    resp = client.get("/tasks", params={"status": "queued"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1 and data[0]["id"] == "a"


def test_cancel_task(client):
    tasks_router.TASK_STORE["x"] = tasks_router.TaskRecord(
        id="x", name="t1", status="queued", created_at=tasks_router.datetime.now(tasks_router.timezone.utc)
    )
    resp = client.delete("/tasks/x")
    assert resp.status_code == 200
    assert tasks_router.TASK_STORE["x"].status == "cancelled"
