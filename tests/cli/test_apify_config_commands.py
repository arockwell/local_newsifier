import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from local_newsifier.cli.main import cli


# Example configurations used across tests
EXAMPLE_CONFIGS = [
    {
        "id": 1,
        "name": "News Scraper",
        "actor_id": "actor1",
        "source_type": "news",
        "is_active": True,
        "last_run_at": "2024-01-01T10:00:00",
        "input_configuration": {"foo": "bar"},
    },
    {
        "id": 2,
        "name": "Blog Scraper",
        "actor_id": "actor2",
        "source_type": "blog",
        "is_active": False,
        "last_run_at": None,
        "input_configuration": {},
    },
]


@patch("local_newsifier.cli.commands.apify_config.get_injected_obj")
def test_list_configs_table_output(mock_get_injected_obj):
    """Verify table output of the list command."""
    mock_service = MagicMock()
    mock_service.list_configs.return_value = EXAMPLE_CONFIGS
    mock_get_injected_obj.return_value = mock_service

    runner = CliRunner()
    result = runner.invoke(cli, ["apify-config", "list"])

    assert result.exit_code == 0
    assert "News Scraper" in result.output
    assert "Blog Scraper" in result.output
    assert "actor1" in result.output
    assert "actor2" in result.output
    mock_service.list_configs.assert_called_once_with(
        skip=0, limit=100, active_only=False, source_type=None
    )


@patch("local_newsifier.cli.commands.apify_config.get_injected_obj")
def test_list_configs_json_output(mock_get_injected_obj):
    """Verify JSON output of the list command."""
    mock_service = MagicMock()
    mock_service.list_configs.return_value = EXAMPLE_CONFIGS
    mock_get_injected_obj.return_value = mock_service

    runner = CliRunner()
    result = runner.invoke(cli, ["apify-config", "list", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["name"] == "News Scraper"
    assert data[1]["name"] == "Blog Scraper"


@patch("local_newsifier.cli.commands.apify_config.get_injected_obj")
def test_list_configs_filters(mock_get_injected_obj):
    """Verify filtering options call the service with correct parameters."""
    mock_service = MagicMock()
    mock_service.list_configs.return_value = EXAMPLE_CONFIGS[:1]
    mock_get_injected_obj.return_value = mock_service

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["apify-config", "list", "--active-only", "--source-type", "news"],
    )

    assert result.exit_code == 0
    mock_service.list_configs.assert_called_once_with(
        skip=0, limit=100, active_only=True, source_type="news"
    )
    assert "News Scraper" in result.output

