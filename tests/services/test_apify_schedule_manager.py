"""Tests for the ApifyScheduleManager service."""

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from local_newsifier.crud.apify_source_config import CRUDApifySourceConfig
from local_newsifier.models.apify import ApifySourceConfig
from local_newsifier.services.apify_schedule_manager import ApifyScheduleManager
from local_newsifier.services.apify_service import ApifyService


@pytest.fixture
def mock_apify_service():
    """Create a mock ApifyService."""
    mock_service = MagicMock(spec=ApifyService)

    # Set up mock responses
    mock_service.create_schedule.return_value = {
        "id": "mock_schedule_id",
        "name": "Test Schedule",
        "cronExpression": "0 0 * * *",
        "isEnabled": True,
        "actId": "mock_actor_id",
    }

    mock_service.update_schedule.return_value = {
        "id": "mock_schedule_id",
        "name": "Updated Schedule",
        "cronExpression": "0 0 * * *",
        "isEnabled": True,
        "actId": "mock_actor_id",
    }

    mock_service.delete_schedule.return_value = {
        "id": "mock_schedule_id",
        "deleted": True,
    }

    mock_service.get_schedule.return_value = {
        "id": "mock_schedule_id",
        "name": "Test Schedule",
        "cronExpression": "0 0 * * *",
        "isEnabled": True,
        "actId": "mock_actor_id",
    }

    mock_service.list_schedules.return_value = {
        "data": {
            "items": [
                {
                    "id": "mock_schedule_id",
                    "name": "Local Newsifier: Test Config",
                    "cronExpression": "0 0 * * *",
                    "isEnabled": True,
                    "actId": "mock_actor_id",
                }
            ],
            "total": 1,
        }
    }

    return mock_service


@pytest.fixture
def mock_config_crud():
    """Create a mock CRUDApifySourceConfig."""
    mock_crud = MagicMock(spec=CRUDApifySourceConfig)

    # Create a mock config
    config1 = ApifySourceConfig(
        id=1,
        name="Test Config",
        actor_id="mock_actor_id",
        is_active=True,
        schedule="0 0 * * *",
        schedule_id=None,
        source_type="test",
        input_configuration={"test": "value"},
        last_run_at=None,
    )

    config2 = ApifySourceConfig(
        id=2,
        name="Existing Schedule Config",
        actor_id="mock_actor_id",
        is_active=True,
        schedule="0 0 * * *",
        schedule_id="mock_schedule_id",
        source_type="test",
        input_configuration={"test": "value"},
        last_run_at=None,
    )

    # Set up mock crud methods
    mock_crud.get.side_effect = lambda session, id: (
        config1 if id == 1 else config2 if id == 2 else None
    )
    mock_crud.get_scheduled_configs.return_value = [config1, config2]
    mock_crud.get_configs_with_schedule_ids.return_value = [config2]

    return mock_crud


@pytest.fixture
def mock_session():
    """Create a mock session."""
    return MagicMock(spec=Session)


@pytest.fixture
def schedule_manager(mock_apify_service, mock_config_crud, mock_session):
    """Create an ApifyScheduleManager with mock dependencies."""

    def session_factory():
        return mock_session

    return ApifyScheduleManager(
        apify_service=mock_apify_service,
        apify_source_config_crud=mock_config_crud,
        session_factory=session_factory,
    )


def test_create_schedule_for_config(
    schedule_manager, mock_apify_service, mock_config_crud, mock_session
):
    """Test creating a schedule for a config."""
    # Test successful creation
    result = schedule_manager.create_schedule_for_config(1)

    # Verify interactions
    mock_apify_service.create_schedule.assert_called_once_with(
        actor_id="moJRLRc85AitArpNN",  # This matches the hardcoded ID in the service
        cron_expression="0 0 * * *",
        run_input={"test": "value"},
        name="Local Newsifier: Test Config",
    )

    mock_config_crud.update.assert_called_once()
    assert result is True

    # Reset mocks
    mock_apify_service.create_schedule.reset_mock()
    mock_config_crud.update.reset_mock()

    # Test with existing schedule - should return False
    mock_apify_service.get_schedule.return_value = {"id": "mock_schedule_id"}
    result = schedule_manager.create_schedule_for_config(2)

    # Verify no new schedule was created
    mock_apify_service.create_schedule.assert_not_called()
    assert result is False


def test_update_schedule_for_config(
    schedule_manager, mock_apify_service, mock_config_crud, mock_session
):
    """Test updating a schedule for a config."""
    # Test successful update with changes
    mock_apify_service.get_schedule.return_value = {
        "id": "mock_schedule_id",
        "name": "Old Name",
        "cronExpression": "0 0 * * 0",  # Different from config
        "isEnabled": True,
        "actId": "mock_actor_id",
        "runInput": {"old": "value"},
    }

    result = schedule_manager.update_schedule_for_config(2)

    # Verify interactions
    mock_apify_service.update_schedule.assert_called_once()
    assert result is True

    # Reset mocks
    mock_apify_service.get_schedule.reset_mock()
    mock_apify_service.update_schedule.reset_mock()

    # Test with no changes needed
    mock_apify_service.get_schedule.return_value = {
        "id": "mock_schedule_id",
        "name": "local-newsifier-existing-schedule-config",  # Sanitized name format
        "cronExpression": "0 0 * * *",  # Same as config
        "isEnabled": True,
        "actId": "mock_actor_id",
        "runInput": {"test": "value"},  # Same as config
    }

    result = schedule_manager.update_schedule_for_config(2)

    # Verify no update was needed
    mock_apify_service.update_schedule.assert_not_called()
    assert result is False


def test_delete_schedule_for_config(
    schedule_manager, mock_apify_service, mock_config_crud, mock_session
):
    """Test deleting a schedule for a config."""
    # Test successful deletion
    result = schedule_manager.delete_schedule_for_config(2)

    # Verify interactions
    mock_apify_service.delete_schedule.assert_called_once_with("mock_schedule_id")
    mock_config_crud.update.assert_called_once()
    assert result is True

    # Reset mocks
    mock_apify_service.delete_schedule.reset_mock()
    mock_config_crud.update.reset_mock()

    # Test with no schedule to delete
    result = schedule_manager.delete_schedule_for_config(1)

    # Verify no deletion attempted
    mock_apify_service.delete_schedule.assert_not_called()
    assert result is False


def test_verify_schedule_status(
    schedule_manager, mock_apify_service, mock_config_crud, mock_session
):
    """Test verifying schedule status."""
    # Test with existing schedule in sync
    mock_apify_service.get_schedule.return_value = {
        "id": "mock_schedule_id",
        "name": "Local Newsifier: Existing Schedule Config",
        "cronExpression": "0 0 * * *",  # Same as config
        "isEnabled": True,  # Same as config
        "actId": "mock_actor_id",  # Same as config
    }

    result = schedule_manager.verify_schedule_status(2)

    # Verify expected result structure
    assert result["exists"] is True
    assert result["synced"] is True
    assert "schedule_details" in result
    assert "config_details" in result

    # Test with existing schedule out of sync
    mock_apify_service.get_schedule.return_value = {
        "id": "mock_schedule_id",
        "name": "Local Newsifier: Existing Schedule Config",
        "cronExpression": "0 0 * * 1",  # Different from config
        "isEnabled": True,
        "actId": "mock_actor_id",
    }

    result = schedule_manager.verify_schedule_status(2)

    # Verify expected result
    assert result["exists"] is True
    assert result["synced"] is False

    # Test with non-existent schedule
    from local_newsifier.errors.error import ServiceError

    mock_apify_service.get_schedule.side_effect = ServiceError(
        service="apify", error_type="not_found", message="Schedule not found"
    )

    result = schedule_manager.verify_schedule_status(2)

    # Verify expected result
    assert result["exists"] is False
    assert result["synced"] is False


def test_sync_schedules(schedule_manager, mock_apify_service, mock_config_crud, mock_session):
    """Test synchronizing all schedules."""
    # Mock the individual operations
    with patch.object(
        schedule_manager, "create_schedule_for_config", return_value=True
    ) as mock_create:
        with patch.object(
            schedule_manager, "update_schedule_for_config", return_value=True
        ) as mock_update:
            with patch.object(
                schedule_manager, "_clean_orphaned_schedules", return_value=1
            ) as mock_clean:

                result = schedule_manager.sync_schedules()

                # Verify interactions
                assert mock_create.call_count == 1  # For config without schedule_id
                assert mock_update.call_count == 1  # For config with schedule_id
                assert mock_clean.call_count == 1

                # Verify result structure
                assert result["created"] == 1
                assert result["updated"] == 1
                assert result["deleted"] == 1
                assert result["unchanged"] == 0
                assert len(result["errors"]) == 0


def test_clean_orphaned_schedules(
    schedule_manager, mock_apify_service, mock_config_crud, mock_session
):
    """Test cleaning orphaned schedules."""
    # Set up the session exec mock to return config IDs
    mock_session.exec.return_value.all.return_value = [
        MagicMock(schedule_id="mock_schedule_id")  # This one will be kept
    ]

    # Add an orphaned schedule to the list
    mock_apify_service.list_schedules.return_value = {
        "data": {
            "items": [
                {
                    "id": "mock_schedule_id",  # This one will be kept
                    "name": "Local Newsifier: Test Config",
                    "cronExpression": "0 0 * * *",
                    "isEnabled": True,
                    "actId": "mock_actor_id",
                },
                {
                    "id": "orphaned_schedule_id",  # This one should be deleted
                    "name": "Local Newsifier: Orphaned Config",
                    "cronExpression": "0 0 * * *",
                    "isEnabled": True,
                    "actId": "mock_actor_id",
                },
            ],
            "total": 2,
        }
    }

    # Call the method under test
    deleted = schedule_manager._clean_orphaned_schedules(mock_session)

    # Verify interactions
    mock_apify_service.delete_schedule.assert_called_once_with("orphaned_schedule_id")
    assert deleted == 1
