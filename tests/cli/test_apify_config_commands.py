# Tests for the Apify config CLI commands.

import json
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from local_newsifier.cli.main import cli


@pytest.fixture
def mock_config_service(monkeypatch):
    """Patch dependency injection to provide a mock service."""
    service = MagicMock()
    session_gen = MagicMock()
    session_gen.__next__.return_value = MagicMock()
    crud = MagicMock()

    from local_newsifier.di import providers as p

    def fake_get_injected_obj(provider, **kwargs):
        if provider == p.get_session:
            return session_gen
        if provider == p.get_apify_source_config_crud:
            return crud
        if provider == p.get_apify_source_config_service:
            return service
        return MagicMock()

    monkeypatch.setattr(
        "local_newsifier.cli.commands.apify_config.get_injected_obj",
        fake_get_injected_obj,
    )
    return service


@pytest.fixture
def runner():
    return CliRunner()


def test_list_configs(runner, mock_config_service):
    mock_config_service.list_configs.return_value = [
        {
            "id": 1,
            "name": "Test Config",
            "actor_id": "actor1",
            "source_type": "news",
            "is_active": True,
            "last_run_at": None,
            "input_configuration": {},
        }
    ]

    result = runner.invoke(cli, ["apify-config", "list"])

    assert result.exit_code == 0
    assert "Test Config" in result.output
    mock_config_service.list_configs.assert_called_once()


def test_add_config(runner, mock_config_service):
    mock_config_service.create_config.return_value = {
        "id": 1,
        "name": "Test Config",
        "actor_id": "actor1",
        "source_type": "news",
    }

    result = runner.invoke(
        cli,
        [
            "apify-config",
            "add",
            "--name",
            "Test Config",
            "--actor-id",
            "actor1",
            "--source-type",
            "news",
        ],
    )

    assert result.exit_code == 0
    assert "added successfully" in result.output
    mock_config_service.create_config.assert_called_once_with(
        name="Test Config",
        actor_id="actor1",
        source_type="news",
        source_url=None,
        schedule=None,
        input_configuration=None,
    )


def test_show_config(runner, mock_config_service):
    mock_config_service.get_config.return_value = {
        "id": 1,
        "name": "Test Config",
        "actor_id": "actor1",
        "source_type": "news",
        "source_url": None,
        "is_active": True,
        "schedule": None,
        "last_run_at": None,
        "input_configuration": {},
        "created_at": "2024-01-01T00:00:00",
    }

    result = runner.invoke(cli, ["apify-config", "show", "1"])

    assert result.exit_code == 0
    assert "Configuration #1: Test Config" in result.output
    assert "Actor ID: actor1" in result.output
    mock_config_service.get_config.assert_called_once_with(1)


def test_remove_config(runner, mock_config_service):
    mock_config_service.get_config.return_value = {
        "id": 1,
        "name": "Test Config",
    }
    mock_config_service.remove_config.return_value = True

    result = runner.invoke(
        cli,
        ["apify-config", "remove", "1", "--force"],
    )

    assert result.exit_code == 0
    assert "removed successfully" in result.output
    mock_config_service.get_config.assert_called_once_with(1)
    mock_config_service.remove_config.assert_called_once_with(1)


def test_update_config(runner, mock_config_service):
    mock_config_service.update_config.return_value = {
        "id": 1,
        "name": "Updated Config",
    }

    result = runner.invoke(
        cli,
        [
            "apify-config",
            "update",
            "1",
            "--name",
            "Updated Config",
        ],
    )

    assert result.exit_code == 0
    assert "updated successfully" in result.output
    mock_config_service.update_config.assert_called_once_with(
        config_id=1,
        name="Updated Config",
        actor_id=None,
        source_type=None,
        source_url=None,
        schedule=None,
        is_active=None,
        input_configuration=None,
    )

