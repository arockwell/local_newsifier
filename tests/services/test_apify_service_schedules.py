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


def test_create_schedule(apify_service, mock_apify_client):
    """Test creating a schedule."""
    # Test with required parameters
    result = apify_service.create_schedule(
        actor_id="test_actor_id",
        cron_expression="0 0 * * *"
    )
    
    # Verify interactions
    mock_apify_client.schedules.assert_called_once()
    mock_apify_client.schedules().create.assert_called_once()
    
    # Verify correct parameters
    create_args = mock_apify_client.schedules().create.call_args[0][0]
    assert create_args["actId"] == "test_actor_id"
    assert create_args["cronExpression"] == "0 0 * * *"
    assert create_args["isEnabled"] is True
    
    # Test with optional parameters
    apify_service.create_schedule(
        actor_id="test_actor_id",
        cron_expression="0 0 * * *",
        run_input={"test": "value"},
        name="Custom Schedule Name"
    )
    
    # Verify optional parameters
    create_args = mock_apify_client.schedules().create.call_args[0][0]
    assert create_args["runInput"] == {"test": "value"}
    assert create_args["name"] == "Custom Schedule Name"


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
    mock_apify_client.schedule().update.assert_called_once_with(changes)


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
    # Test without actor_id
    result = apify_service.list_schedules()
    
    # Verify interactions
    mock_apify_client.schedules.assert_called()
    mock_apify_client.schedules().list.assert_called_with({})
    
    # Test with actor_id
    result = apify_service.list_schedules(actor_id="test_actor_id")
    
    # Verify filter is applied
    mock_apify_client.schedules().list.assert_called_with({"filter": {"actId": "test_actor_id"}})


def test_test_mode_schedule_operations():
    """Test schedule operations in test mode."""
    # Create service in test mode
    service = ApifyService(test_mode=True)
    
    # Test create_schedule
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
    
    # Test list_schedules with actor_id
    list_filtered_result = service.list_schedules(actor_id="test_actor_id")
    assert len(list_filtered_result["data"]["items"]) == 1
    assert list_filtered_result["data"]["items"][0]["actId"] == "test_actor_id"