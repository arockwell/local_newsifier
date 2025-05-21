import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from local_newsifier.cli.commands.apify_config import (
    add_config,
    get_apify_source_config_crud,
    get_apify_source_config_service,
    get_session,
    list_configs,
    remove_config,
    show_config,
    update_config,
)


@pytest.fixture
def sample_config():
    return {
        "id": 1,
        "name": "Test Config",
        "actor_id": "actor123",
        "source_type": "news",
        "source_url": "https://example.com",
        "schedule": "0 0 * * *",
        "is_active": True,
        "input_configuration": {"foo": "bar"},
        "last_run_at": "2024-01-01T00:00:00",
        "created_at": "2024-01-01T00:00:00",
    }


def setup_injection(mock_get_injected_obj, service):
    session = MagicMock()
    session_gen = MagicMock()
    session_gen.__next__.return_value = session
    crud = MagicMock()

    def side_effect(provider, **kwargs):
        if provider == get_session:
            return session_gen
        if provider == get_apify_source_config_crud:
            return crud
        if provider == get_apify_source_config_service:
            return service
        return MagicMock()

    mock_get_injected_obj.side_effect = side_effect


@patch("local_newsifier.cli.commands.apify_config.get_injected_obj")
def test_list_configs(mock_get_injected_obj, sample_config):
    service = MagicMock()
    service.list_configs.return_value = [sample_config]
    setup_injection(mock_get_injected_obj, service)

    runner = CliRunner()
    result = runner.invoke(list_configs)

    assert result.exit_code == 0
    assert "Test Config" in result.output
    assert "actor123" in result.output
    service.list_configs.assert_called_once_with(
        skip=0, limit=100, active_only=False, source_type=None
    )


@patch("local_newsifier.cli.commands.apify_config.get_injected_obj")
def test_add_config(mock_get_injected_obj, sample_config):
    service = MagicMock()
    service.create_config.return_value = sample_config
    setup_injection(mock_get_injected_obj, service)

    runner = CliRunner()
    result = runner.invoke(
        add_config,
        ["--name", "Test Config", "--actor-id", "actor123", "--source-type", "news"],
    )

    assert result.exit_code == 0
    assert "Apify source configuration added successfully" in result.output
    service.create_config.assert_called_once_with(
        name="Test Config",
        actor_id="actor123",
        source_type="news",
        source_url=None,
        schedule=None,
        input_configuration=None,
    )


@patch("local_newsifier.cli.commands.apify_config.get_injected_obj")
def test_show_config(mock_get_injected_obj, sample_config):
    service = MagicMock()
    service.get_config.return_value = sample_config
    setup_injection(mock_get_injected_obj, service)

    runner = CliRunner()
    result = runner.invoke(show_config, ["1"])

    assert result.exit_code == 0
    assert "Configuration #1: Test Config" in result.output
    assert "Actor ID: actor123" in result.output
    service.get_config.assert_called_once_with(1)


@patch("local_newsifier.cli.commands.apify_config.get_injected_obj")
def test_remove_config(mock_get_injected_obj, sample_config):
    service = MagicMock()
    service.get_config.return_value = sample_config
    service.remove_config.return_value = True
    setup_injection(mock_get_injected_obj, service)

    runner = CliRunner()
    result = runner.invoke(remove_config, ["1", "--force"])

    assert result.exit_code == 0
    assert "removed successfully" in result.output
    service.get_config.assert_called_once_with(1)
    service.remove_config.assert_called_once_with(1)


@patch("local_newsifier.cli.commands.apify_config.get_injected_obj")
def test_update_config(mock_get_injected_obj, sample_config):
    updated = sample_config.copy()
    updated["name"] = "Updated"
    service = MagicMock()
    service.update_config.return_value = updated
    setup_injection(mock_get_injected_obj, service)

    runner = CliRunner()
    result = runner.invoke(update_config, ["1", "--name", "Updated"])

    assert result.exit_code == 0
    assert "updated successfully" in result.output
    service.update_config.assert_called_once_with(
        config_id=1,
        name="Updated",
        actor_id=None,
        source_type=None,
        source_url=None,
        schedule=None,
        is_active=False,
        input_configuration=None,
    )
