"""Tests for ApifySourceConfigService."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session

from local_newsifier.errors.error import ServiceError
from local_newsifier.models.apify import ApifySourceConfig
from local_newsifier.services.apify_source_config_service import ApifySourceConfigService


class TestApifySourceConfigService:
    """Tests for ApifySourceConfigService."""

    @pytest.fixture
    def mock_crud(self):
        """Create a mock CRUD for testing."""
        return Mock()

    @pytest.fixture
    def mock_apify_service(self):
        """Create a mock ApifyService for testing."""
        return Mock()

    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Create a mock session factory for testing."""
        from contextlib import contextmanager

        @contextmanager
        def session_context():
            try:
                yield mock_session
            finally:
                pass

        # Create a mock that returns the context manager
        mock_factory = Mock()
        mock_factory.return_value = session_context()

        return mock_factory

    @pytest.fixture
    def service(self, mock_crud, mock_apify_service, mock_session_factory):
        """Create a service instance for testing."""
        return ApifySourceConfigService(
            apify_source_config_crud=mock_crud,
            apify_service=mock_apify_service,
            session_factory=mock_session_factory,
        )

    def test_list_configs(self, service, mock_crud, mock_session_factory, mock_session):
        """Test listing all configs."""
        # Setup mock
        mock_configs = [
            ApifySourceConfig(
                id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=True
            )
        ]
        mock_crud.get_multi.return_value = mock_configs

        # Call function
        result = service.list_configs(skip=0, limit=10)

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get_multi.assert_called_once_with(mock_session, skip=0, limit=10)
        assert len(result) == 1
        assert result[0]["name"] == "Test Config"
        assert result[0]["actor_id"] == "test-actor"

    def test_list_configs_active_only(self, service, mock_crud, mock_session_factory, mock_session):
        """Test listing active configs only."""
        # Setup mock
        mock_configs = [
            ApifySourceConfig(
                id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=True
            )
        ]
        mock_crud.get_active_configs.return_value = mock_configs

        # Call function
        result = service.list_configs(active_only=True)

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get_active_configs.assert_called_once_with(mock_session, skip=0, limit=100)
        assert len(result) == 1
        assert result[0]["name"] == "Test Config"

    def test_list_configs_by_source_type(
        self, service, mock_crud, mock_session_factory, mock_session
    ):
        """Test listing configs by source type."""
        # Setup mock
        mock_configs = [
            ApifySourceConfig(
                id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=True
            )
        ]
        mock_crud.get_by_source_type.return_value = mock_configs

        # Call function
        result = service.list_configs(source_type="news")

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get_by_source_type.assert_called_once_with(mock_session, source_type="news")
        assert len(result) == 1
        assert result[0]["source_type"] == "news"

    def test_get_config(self, service, mock_crud, mock_session_factory, mock_session):
        """Test getting a specific config."""
        # Setup mock
        mock_config = ApifySourceConfig(
            id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=True
        )
        mock_crud.get.return_value = mock_config

        # Call function
        result = service.get_config(config_id=1)

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get.assert_called_once_with(mock_session, id=1)
        assert result["id"] == 1
        assert result["name"] == "Test Config"

    def test_get_config_not_found(self, service, mock_crud, mock_session_factory, mock_session):
        """Test getting a non-existent config."""
        # Setup mock
        mock_crud.get.return_value = None

        # Call function
        result = service.get_config(config_id=999)

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get.assert_called_once_with(mock_session, id=999)
        assert result is None

    def test_create_config(self, service, mock_crud, mock_session_factory, mock_session):
        """Test creating a new config."""
        # Setup mock
        mock_config = ApifySourceConfig(
            id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=True
        )
        mock_crud.create.return_value = mock_config

        # Call function
        result = service.create_config(
            name="Test Config", actor_id="test-actor", source_type="news"
        )

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.create.assert_called_once()
        assert result["id"] == 1
        assert result["name"] == "Test Config"
        assert result["actor_id"] == "test-actor"
        assert result["source_type"] == "news"

    def test_create_config_error(self, service, mock_crud, mock_session_factory, mock_session):
        """Test creating a config with error."""
        # Setup mock
        mock_crud.create.side_effect = ServiceError(
            service="apify",
            error_type="validation",
            message="Config with this name already exists",
            context={"name": "Test Config"},
        )

        # Call function and verify exception
        with pytest.raises(ServiceError) as exc_info:
            service.create_config(name="Test Config", actor_id="test-actor", source_type="news")

        # Verify
        assert "Config with this name already exists" in str(exc_info.value)
        mock_session_factory.assert_called_once()

    def test_update_config(self, service, mock_crud, mock_session_factory, mock_session):
        """Test updating a config."""
        # Setup mock
        mock_config = ApifySourceConfig(
            id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=True
        )
        updated_config = ApifySourceConfig(
            id=1, name="Updated Config", actor_id="test-actor", source_type="news", is_active=True
        )
        mock_crud.get.return_value = mock_config
        mock_crud.update.return_value = updated_config

        # Call function
        result = service.update_config(config_id=1, name="Updated Config")

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get.assert_called_once_with(mock_session, id=1)
        mock_crud.update.assert_called_once()
        assert result["id"] == 1
        assert result["name"] == "Updated Config"

    def test_update_config_not_found(self, service, mock_crud, mock_session_factory, mock_session):
        """Test updating a non-existent config."""
        # Setup mock
        mock_crud.get.return_value = None

        # Call function
        result = service.update_config(config_id=999, name="Updated Config")

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get.assert_called_once_with(mock_session, id=999)
        assert result is None

    def test_remove_config(self, service, mock_crud, mock_session_factory, mock_session):
        """Test removing a config."""
        # Setup mock
        mock_config = ApifySourceConfig(
            id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=True
        )
        mock_crud.get.return_value = mock_config
        mock_crud.remove.return_value = mock_config

        # Call function
        result = service.remove_config(config_id=1)

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.remove.assert_called_once_with(mock_session, id=1)
        assert result is True

    def test_toggle_active(self, service, mock_crud, mock_session_factory, mock_session):
        """Test toggling active status."""
        # Setup mock
        mock_config = ApifySourceConfig(
            id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=False
        )
        mock_crud.toggle_active.return_value = mock_config

        # Call function
        result = service.toggle_active(config_id=1, is_active=False)

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.toggle_active.assert_called_once_with(mock_session, config_id=1, is_active=False)
        assert result["is_active"] is False

    def test_run_configuration(
        self, service, mock_crud, mock_apify_service, mock_session_factory, mock_session
    ):
        """Test running a configuration."""
        # Setup mock
        mock_config = ApifySourceConfig(
            id=1,
            name="Test Config",
            actor_id="test-actor",
            source_type="news",
            is_active=True,
            input_configuration={"url": "https://example.com"},
        )
        mock_crud.get.return_value = mock_config
        mock_apify_service.run_actor.return_value = {
            "id": "run123",
            "defaultDatasetId": "dataset123",
        }

        # Call function
        result = service.run_configuration(config_id=1)

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get.assert_called_once_with(mock_session, id=1)
        mock_crud.update_last_run.assert_called_once()
        mock_apify_service.run_actor.assert_called_once_with(
            actor_id="test-actor", run_input={"url": "https://example.com"}
        )
        assert result["status"] == "success"
        assert result["config_id"] == 1
        assert result["config_name"] == "Test Config"
        assert result["actor_id"] == "test-actor"
        assert result["run_id"] == "run123"
        assert result["dataset_id"] == "dataset123"

    def test_run_configuration_not_found(
        self, service, mock_crud, mock_session_factory, mock_session
    ):
        """Test running a non-existent configuration."""
        # Setup mock
        mock_crud.get.return_value = None

        # Call function and verify exception
        with pytest.raises(ServiceError) as exc_info:
            service.run_configuration(config_id=999)

        # Verify
        assert "Configuration with ID 999 not found" in str(exc_info.value)
        mock_session_factory.assert_called_once()
        mock_crud.get.assert_called_once_with(mock_session, id=999)

    def test_run_configuration_inactive(
        self, service, mock_crud, mock_session_factory, mock_session
    ):
        """Test running an inactive configuration."""
        # Setup mock
        mock_config = ApifySourceConfig(
            id=1, name="Test Config", actor_id="test-actor", source_type="news", is_active=False
        )
        mock_crud.get.return_value = mock_config

        # Call function and verify exception
        with pytest.raises(ServiceError) as exc_info:
            service.run_configuration(config_id=1)

        # Verify
        assert "Configuration 'Test Config' is not active" in str(exc_info.value)
        mock_session_factory.assert_called_once()
        mock_crud.get.assert_called_once_with(mock_session, id=1)

    def test_get_scheduled_configs(self, service, mock_crud, mock_session_factory, mock_session):
        """Test getting scheduled configurations."""
        # Setup mock
        mock_configs = [
            ApifySourceConfig(
                id=1,
                name="Test Config",
                actor_id="test-actor",
                source_type="news",
                is_active=True,
                schedule="0 * * * *",
            )
        ]
        mock_crud.get_scheduled_configs.return_value = mock_configs

        # Call function
        result = service.get_scheduled_configs()

        # Verify
        mock_session_factory.assert_called_once()
        mock_crud.get_scheduled_configs.assert_called_once_with(mock_session, enabled_only=True)
        assert len(result) == 1
        assert result[0]["schedule"] == "0 * * * *"
