"""Tests for the state model."""

from datetime import datetime

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState


def test_state_management():
    """Test state management functionality."""
    state = NewsAnalysisState(target_url="https://example.com/news/1")

    # Test logging
    state.add_log("Test message")
    assert len(state.run_logs) == 1
    assert "Test message" in state.run_logs[0]

    # Test error handling
    error = ValueError("Test error")
    state.set_error("test_task", error)
    assert state.error_details.task == "test_task"
    assert state.error_details.type == "ValueError"
    assert state.error_details.message == "Test error"

    # Test timestamps
    assert isinstance(state.created_at, datetime)
    assert isinstance(state.last_updated, datetime)

    # Test touch
    original_updated = state.last_updated
    state.touch()
    assert state.last_updated > original_updated
