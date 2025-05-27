"""Tests for the BaseState model."""

from datetime import datetime, timezone
from enum import Enum

import pytest

from local_newsifier.errors.error import ServiceError
from local_newsifier.models.base_state import BaseState, extract_error_details


class DummyStatus(str, Enum):
    """Simple status enum for testing."""

    STARTED = "STARTED"
    FAILED = "FAILED"


class DummyState(BaseState):
    """Minimal BaseState subclass for tests."""

    status: DummyStatus = DummyStatus.STARTED
    failure_status: DummyStatus = DummyStatus.FAILED


def test_add_log_appends_message_and_updates_timestamp():
    """add_log should append a timestamped message and update last_updated."""
    state = DummyState()
    state.last_updated = datetime(2000, 1, 1, tzinfo=timezone.utc)

    state.add_log("Processing started")

    assert len(state.run_logs) == 1
    assert "Processing started" in state.run_logs[0]
    assert state.last_updated > datetime(2000, 1, 1, tzinfo=timezone.utc)


def test_set_error_updates_status_and_touches():
    """set_error should populate error_details, update status and touch."""
    state = DummyState()
    state.last_updated = datetime(2000, 1, 1, tzinfo=timezone.utc)

    state.set_error("task", ValueError("boom"))

    assert state.error_details is not None
    assert state.error_details.task == "task"
    assert state.error_details.type == "ValueError"
    assert state.error_details.message == "boom"
    assert state.status == DummyStatus.FAILED
    assert state.last_updated > datetime(2000, 1, 1, tzinfo=timezone.utc)


def test_extract_error_details_unwraps_service_error():
    """extract_error_details should unwrap ServiceError original exception."""
    original = RuntimeError("oops")
    error = ServiceError("test", "server", "failure", original=original)

    err_type, message, tb = extract_error_details(error)

    assert err_type == "RuntimeError"
    assert message == "oops"
    assert isinstance(tb, str)
