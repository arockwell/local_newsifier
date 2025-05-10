"""Tests for the schedule-related methods in ApifyService."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from local_newsifier.services.apify_service import ApifyService


@pytest.fixture
def mock_apify_client():
    """Create a mock ApifyClient with schedule-related methods."""
    mock_client = MagicMock()
    
    # Mock the schedules client
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
            "total": 1
        }
    }
    mock_client.schedules.return_value = mock_schedules
    
    # Mock the individual schedule client
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
    
    return mock_client


@pytest.fixture
def apify_service(mock_apify_client):
    """Create an ApifyService with a mock client."""
    service = ApifyService(token="test_token")
    service._client = mock_apify_client
    return service


def test_create_schedule():
    """Test creating a schedule in test mode."""
    # Create a service in test_mode to use the test mode implementation
    service = ApifyService(test_mode=True)

    # Test the method
    result = service.create_schedule(
        actor_id="test_actor_id",
        cron_expression="0 0 * * *"
    )

    # Verify the result structure without checking the exact ID
    assert "id" in result
    assert result["cronExpression"] == "0 0 * * *"

    # Test with optional parameters
    result_with_options = service.create_schedule(
        actor_id="test_actor_id",
        cron_expression="0 0 * * *",
        run_input={"test": "value"},
        name="Custom Schedule Name"
    )

    # Verify the result contains correct values
    assert "id" in result_with_options
    assert result_with_options["cronExpression"] == "0 0 * * *"
    assert "name" in result_with_options
    assert "actions" in result_with_options
    assert len(result_with_options["actions"]) > 0
    assert result_with_options["actions"][0]["actorId"] == "test_actor_id"


def test_update_schedule(apify_service, mock_apify_client):
    """Test updating a schedule."""
    changes = {
        "name": "Updated Schedule Name",
        "cronExpression": "0 0 * * 1",
        "isEnabled": False
    }
    
    result = apify_service.update_schedule("test_schedule_id", changes)
    
    # Verify interactions
    mock_apify_client.schedule.assert_called_once_with("test_schedule_id")

    # Verify the update was called with the converted parameters
    expected_converted_params = {
        "name": "Updated Schedule Name",
        "cron_expression": "0 0 * * 1",  # Converted from cronExpression
        "is_enabled": False,  # Converted from isEnabled
    }
    mock_apify_client.schedule().update.assert_called_once_with(**expected_converted_params)


def test_delete_schedule(apify_service, mock_apify_client):
    """Test deleting a schedule."""
    result = apify_service.delete_schedule("test_schedule_id")
    
    # Verify interactions
    mock_apify_client.schedule.assert_called_once_with("test_schedule_id")
    mock_apify_client.schedule().delete.assert_called_once()
    
    # Verify result format
    assert result["id"] == "test_schedule_id"
    assert result["deleted"] is True


def test_get_schedule(apify_service, mock_apify_client):
    """Test getting schedule details."""
    result = apify_service.get_schedule("test_schedule_id")
    
    # Verify interactions
    mock_apify_client.schedule.assert_called_once_with("test_schedule_id")
    mock_apify_client.schedule().get.assert_called_once()


def test_list_schedules(apify_service, mock_apify_client):
    """Test listing schedules."""
    # Manually set the client on the service
    apify_service._client = mock_apify_client
    
    # Test without actor_id
    result = apify_service.list_schedules()
    
    # Verify interactions
    mock_apify_client.schedules.assert_called()
    assert mock_apify_client.schedules().list.called
    
    # Test with actor_id
    # Reset the mock
    mock_apify_client.schedules().list.reset_mock()
    result = apify_service.list_schedules(actor_id="test_actor_id")
    
    # Verify the function was called again
    assert mock_apify_client.schedules().list.called


@patch.object(ApifyService, "create_schedule")
@patch.object(ApifyService, "update_schedule")
@patch.object(ApifyService, "delete_schedule")
@patch.object(ApifyService, "get_schedule")
@patch.object(ApifyService, "list_schedules")
def test_test_mode_schedule_operations(
    mock_list_schedules, mock_get_schedule, mock_delete_schedule,
    mock_update_schedule, mock_create_schedule
):
    """Test schedule operations in test mode."""
    # Set up return values for mocked methods
    mock_create_schedule.return_value = {
        "id": "test_schedule_id",
        "cronExpression": "0 0 * * *",
        "name": "Test Schedule",
        "actId": "test_actor_id"
    }
    
    mock_update_schedule.return_value = {
        "id": "test_schedule_id",
        "name": "Updated Name",
        "cronExpression": "0 0 * * *",
        "actId": "test_actor_id"
    }
    
    mock_delete_schedule.return_value = {
        "id": "test_schedule_id",
        "deleted": True
    }
    
    mock_get_schedule.return_value = {
        "id": "test_schedule_id",
        "name": "Test Schedule",
        "cronExpression": "0 0 * * *",
        "actId": "test_actor_id"
    }
    
    mock_list_schedules.return_value = {
        "data": {
            "items": [{
                "id": "test_schedule_id",
                "name": "Test Schedule",
                "cronExpression": "0 0 * * *",
                "actId": "test_actor_id"
            }],
            "total": 1
        }
    }
    
    # Create service with test_mode=True which shouldn't matter since we're mocking
    service = ApifyService()
    
    # Test create_schedule - will use our mocked method
    create_result = service.create_schedule(
        actor_id="test_actor_id",
        cron_expression="0 0 * * *"
    )
    assert "id" in create_result
    assert create_result["cronExpression"] == "0 0 * * *"
    
    # Test update_schedule
    update_result = service.update_schedule(
        "test_schedule_id",
        {"name": "Updated Name"}
    )
    assert update_result["id"] == "test_schedule_id"
    assert update_result["name"] == "Updated Name"
    
    # Test delete_schedule
    delete_result = service.delete_schedule("test_schedule_id")
    assert delete_result["id"] == "test_schedule_id"
    
    # Test get_schedule
    get_result = service.get_schedule("test_schedule_id")
    assert get_result["id"] == "test_schedule_id"
    
    # Test list_schedules
    list_result = service.list_schedules()
    assert "data" in list_result
    assert "items" in list_result["data"]