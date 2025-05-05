"""Tests for the Apify state models."""
import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4

from local_newsifier.models.apify_state import ApifyIngestState, ApifyBatchIngestState, ApifyIngestStatus
from local_newsifier.models.state import ErrorDetails


class TestApifyIngestState:
    """Test suite for ApifyIngestState class."""
    
    def test_init_defaults(self):
        """Test that default values are set correctly."""
        state = ApifyIngestState()
        assert isinstance(state.run_id, UUID)
        assert state.source_config_id is None
        assert state.actor_id is None
        assert state.status == ApifyIngestStatus.INITIALIZED
        assert len(state.run_logs) == 0
        assert state.error_details is None
        
    def test_add_log(self):
        """Test that logs are added correctly."""
        state = ApifyIngestState()
        state.add_log("Test message")
        assert len(state.run_logs) == 1
        assert "Test message" in state.run_logs[0]
        
    def test_set_error(self):
        """Test error setting."""
        state = ApifyIngestState()
        error = ValueError("Test error")
        state.set_error("test_task", error)
        assert state.error_details is not None
        assert state.error_details.task == "test_task"
        assert "Test error" in state.error_details.message
        
    def test_calculate_metrics(self):
        """Test metrics calculation."""
        state = ApifyIngestState(
            total_items=10,
            processed_items=8,
            failed_items=1,
            skipped_items=1
        )
        state.created_article_ids = [1, 2, 3]
        state.updated_article_ids = [4, 5]
        state.start_time = datetime.now(timezone.utc)
        state.end_time = datetime.now(timezone.utc)
        
        metrics = state.calculate_metrics()
        assert metrics["total_items"] == 10
        assert metrics["processed_items"] == 8
        assert metrics["failed_items"] == 1
        assert metrics["skipped_items"] == 1
        assert metrics["articles_created"] == 3
        assert metrics["articles_updated"] == 2
        assert metrics["success_rate"] == 80.0
        assert "duration_seconds" in metrics
        
    def test_touch_updates_timestamp(self):
        """Test touch method updates timestamp."""
        state = ApifyIngestState()
        original = state.last_updated
        # Ensure some time passes
        state.touch()
        assert state.last_updated >= original


class TestApifyBatchIngestState:
    """Test suite for ApifyBatchIngestState class."""
    
    def test_init_defaults(self):
        """Test that default values are set correctly."""
        state = ApifyBatchIngestState()
        assert isinstance(state.run_id, UUID)
        assert len(state.source_config_ids) == 0
        assert state.status == ApifyIngestStatus.INITIALIZED
        assert state.total_configs == 0
        assert state.processed_configs == 0
        assert state.failed_configs == 0
        assert len(state.run_logs) == 0
        assert state.error_details is None
        
    def test_add_log(self):
        """Test that logs are added correctly."""
        state = ApifyBatchIngestState()
        state.add_log("Test batch message")
        assert len(state.run_logs) == 1
        assert "Test batch message" in state.run_logs[0]
        
    def test_set_error(self):
        """Test error setting."""
        state = ApifyBatchIngestState()
        error = ValueError("Test batch error")
        state.set_error("test_batch_task", error)
        assert state.error_details is not None
        assert state.error_details.task == "test_batch_task"
        assert "Test batch error" in state.error_details.message
        
    def test_add_sub_state(self):
        """Test adding a sub-state."""
        batch_state = ApifyBatchIngestState(source_config_ids=[1, 2])
        batch_state.total_configs = 2
        
        # Add successful sub-state
        sub_state1 = ApifyIngestState(
            source_config_id=1,
            status=ApifyIngestStatus.COMPLETED_SUCCESS,
            total_items=10,
            processed_items=10
        )
        batch_state.add_sub_state(1, sub_state1)
        assert batch_state.processed_configs == 1
        assert batch_state.failed_configs == 0
        
        # Add failed sub-state
        sub_state2 = ApifyIngestState(
            source_config_id=2,
            status=ApifyIngestStatus.ACTOR_FAILED
        )
        batch_state.add_sub_state(2, sub_state2)
        assert batch_state.processed_configs == 2
        assert batch_state.failed_configs == 1
        
    def test_calculate_metrics(self):
        """Test metrics calculation for batch state."""
        batch_state = ApifyBatchIngestState(source_config_ids=[1, 2])
        batch_state.total_configs = 2
        batch_state.start_time = datetime.now(timezone.utc)
        batch_state.end_time = datetime.now(timezone.utc)
        
        # Add successful sub-state
        sub_state1 = ApifyIngestState(
            source_config_id=1,
            status=ApifyIngestStatus.COMPLETED_SUCCESS,
            total_items=10,
            processed_items=10
        )
        sub_state1.created_article_ids = [1, 2, 3]
        
        # Add failed sub-state
        sub_state2 = ApifyIngestState(
            source_config_id=2,
            status=ApifyIngestStatus.ACTOR_FAILED,
            total_items=5,
            processed_items=0,
            failed_items=5
        )
        
        batch_state.add_sub_state(1, sub_state1)
        batch_state.add_sub_state(2, sub_state2)
        
        metrics = batch_state.calculate_metrics()
        assert metrics["total_configs"] == 2
        assert metrics["processed_configs"] == 2
        assert metrics["failed_configs"] == 1
        assert metrics["success_rate"] == 50.0
        assert metrics["total_items"] == 15
        assert metrics["processed_items"] == 10
        assert metrics["failed_items"] == 5
        assert metrics["articles_created"] == 3
        assert "duration_seconds" in metrics