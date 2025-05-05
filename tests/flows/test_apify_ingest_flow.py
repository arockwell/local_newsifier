"""Tests for the ApifyIngestFlow."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from local_newsifier.flows.apify_ingest_flow import ApifyIngestFlow
from local_newsifier.models.apify_state import ApifyIngestState, ApifyBatchIngestState, ApifyIngestStatus
from local_newsifier.models.state import ErrorDetails


@pytest.fixture
def mock_apify_service():
    """Mock ApifyService."""
    mock_service = MagicMock()
    mock_service.run_actor.return_value = {"id": "test-run-id"}
    mock_service.get_dataset_items.return_value = {"items": [
        {"url": "https://example.com/1", "title": "Article 1", "content": "Content 1"},
        {"url": "https://example.com/2", "title": "Article 2", "content": "Content 2"},
    ]}
    return mock_service


@pytest.fixture
def mock_article_service():
    """Mock ArticleService."""
    return MagicMock()


@pytest.fixture
def mock_source_config_crud():
    """Mock ApifySourceConfigCRUD."""
    mock_crud = MagicMock()
    mock_source_config = MagicMock()
    mock_source_config.id = 1
    mock_source_config.actor_id = "test-actor"
    mock_source_config.default_input = {"start_urls": ["https://example.com"]}
    mock_crud.get.return_value = mock_source_config
    return mock_crud


@pytest.fixture
def mock_article_crud():
    """Mock ArticleCRUD."""
    return MagicMock()


@pytest.fixture
def mock_session():
    """Mock database session."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_session_factory(mock_session):
    """Mock session factory."""
    def _factory():
        return mock_session
    return _factory


@pytest.fixture
def apify_ingest_flow(
    mock_apify_service,
    mock_article_service,
    mock_source_config_crud,
    mock_article_crud,
    mock_session_factory,
):
    """Initialize ApifyIngestFlow with mocks."""
    flow = ApifyIngestFlow(
        apify_service=mock_apify_service,
        article_service=mock_article_service,
        source_config_crud=mock_source_config_crud,
        article_crud=mock_article_crud,
        session_factory=mock_session_factory,
    )
    
    # Add a mock for _wait_for_actor_run that's not part of the service
    flow._wait_for_actor_run = MagicMock(return_value={
        "status": "SUCCEEDED",
        "defaultDatasetId": "test-dataset-id"
    })
    
    # Mock the private methods
    flow._store_dataset_item = MagicMock()
    flow._process_item_to_article = MagicMock(return_value=(MagicMock(id=1), True))
    
    return flow


class TestApifyIngestFlow:
    """Tests for ApifyIngestFlow."""
    
    def test_ingest_from_config_success(self, apify_ingest_flow, mock_apify_service):
        """Test successful ingestion from a single config."""
        # Execute
        state = apify_ingest_flow.ingest_from_config(1)
        
        # Verify
        assert state.status == ApifyIngestStatus.COMPLETED_SUCCESS
        assert state.source_config_id == 1
        assert state.actor_id == "test-actor"
        assert state.apify_run_id == "test-run-id"
        assert state.dataset_id == "test-dataset-id"
        assert state.total_items == 2
        assert state.processed_items == 2
        
        # Verify all steps were called correctly
        mock_apify_service.run_actor.assert_called_once()
        mock_apify_service.get_dataset_items.assert_called_once_with("test-dataset-id")
        apify_ingest_flow._process_item_to_article.assert_called()
        assert apify_ingest_flow._process_item_to_article.call_count == 2
    
    def test_batch_ingest_success(self, apify_ingest_flow):
        """Test successful batch ingestion."""
        # Mock ingest_from_config to return a successful state
        mock_state = ApifyIngestState(
            source_config_id=1,
            status=ApifyIngestStatus.COMPLETED_SUCCESS,
            total_items=2,
            processed_items=2
        )
        apify_ingest_flow.ingest_from_config = MagicMock(return_value=mock_state)
        
        # Execute
        state = apify_ingest_flow.batch_ingest([1, 2])
        
        # Verify
        assert state.status == ApifyIngestStatus.COMPLETED_SUCCESS
        assert state.total_configs == 2
        assert state.processed_configs == 2
        assert state.failed_configs == 0
        
        # Verify ingest_from_config was called for each config
        assert apify_ingest_flow.ingest_from_config.call_count == 2
    
    def test_ingest_from_config_actor_failure(self, apify_ingest_flow, mock_apify_service):
        """Test ingestion with actor failure."""
        # Set up the actor run to fail
        mock_apify_service.run_actor.side_effect = Exception("Actor run failed")
        
        # Execute
        state = apify_ingest_flow.ingest_from_config(1)
        
        # Verify
        assert state.status == ApifyIngestStatus.ACTOR_FAILED
        assert state.error_details is not None
        if state.error_details:  # Type checking to satisfy the null check above
            assert "Actor run failed" in state.error_details.message
    
    def test_ingest_from_config_processing_partial(self, apify_ingest_flow):
        """Test ingestion with partial processing success."""
        # Set up the processing to partially succeed
        def mock_process_item(session, item, config):
            if item["url"] == "https://example.com/1":
                return (MagicMock(id=1), True)
            return None
        
        apify_ingest_flow._process_item_to_article.side_effect = mock_process_item
        
        # Execute
        state = apify_ingest_flow.ingest_from_config(1)
        
        # Verify
        assert state.status == ApifyIngestStatus.COMPLETED_WITH_ERRORS
        assert state.total_items == 2
        assert state.processed_items == 1
        assert state.failed_items == 1
    
    def test_batch_ingest_partial_failure(self, apify_ingest_flow):
        """Test batch ingestion with some failures."""
        # Mock ingest_from_config to return success for first config and failure for second
        original_method = apify_ingest_flow.ingest_from_config
        
        def mock_ingest(config_id, run_input=None, state=None):
            if config_id == 1:
                return ApifyIngestState(
                    source_config_id=config_id,
                    status=ApifyIngestStatus.COMPLETED_SUCCESS,
                    total_items=2,
                    processed_items=2
                )
            else:
                failed_state = ApifyIngestState(
                    source_config_id=config_id,
                    status=ApifyIngestStatus.ACTOR_FAILED
                )
                failed_state.set_error("test", Exception("Actor run failed"))
                return failed_state
        
        # Replace method with our mock
        apify_ingest_flow.ingest_from_config = MagicMock(side_effect=mock_ingest)
        
        # Execute
        state = apify_ingest_flow.batch_ingest([1, 2])
        
        # Verify
        assert state.status == ApifyIngestStatus.COMPLETED_WITH_ERRORS
        assert state.total_configs == 2
        assert state.processed_configs == 2
        assert state.failed_configs == 1