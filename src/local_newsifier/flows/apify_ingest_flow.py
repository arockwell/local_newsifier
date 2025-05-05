"""Flow for orchestrating the Apify ingestion process."""
from typing import Callable, List, Optional, Dict, Any, Type, Union, Tuple
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session

from local_newsifier.models.apify_state import ApifyIngestState, ApifyBatchIngestState, ApifyIngestStatus
from local_newsifier.models.apify import ApifySourceConfig, ApifyDatasetItem
from local_newsifier.models.article import Article
from local_newsifier.services.apify_service import ApifyService
from local_newsifier.services.article_service import ArticleService
from local_newsifier.crud.apify_source_config import CRUDApifySourceConfig
from local_newsifier.crud.article import ArticleCRUD
from local_newsifier.errors.error import ServiceError


class ApifyIngestFlow:
    """Flow for orchestrating the Apify ingestion process.
    
    This flow handles the entire process of ingesting content from Apify:
    1. Running the appropriate actor based on configuration
    2. Fetching dataset items from the actor run
    3. Processing items into articles
    4. Handling errors and tracking metrics
    
    The flow supports both single source ingestion and batch processing
    of multiple sources.
    """

    def __init__(
        self,
        apify_service: Optional[ApifyService] = None,
        article_service: Optional[ArticleService] = None,
        source_config_crud: Optional[CRUDApifySourceConfig] = None,
        article_crud: Optional[ArticleCRUD] = None,
        session_factory: Optional[Callable[[], Session]] = None,
    ):
        """Initialize the flow with optional dependencies.
        
        Args:
            apify_service: Service for interacting with Apify API
            article_service: Service for article processing
            source_config_crud: CRUD operations for ApifySourceConfig
            article_crud: CRUD operations for Article
            session_factory: Factory for creating database sessions
        """
        self.apify_service = apify_service
        self.article_service = article_service
        self.source_config_crud = source_config_crud
        self.article_crud = article_crud
        self.session_factory = session_factory

    def ingest_from_config(
        self, 
        config_id: int, 
        run_input: Optional[Dict[str, Any]] = None,
        state: Optional[ApifyIngestState] = None
    ) -> ApifyIngestState:
        """Ingest content from a specific source configuration.
        
        Args:
            config_id: ID of the ApifySourceConfig to use
            run_input: Optional custom input for the actor run
            state: Optional existing state to continue from
            
        Returns:
            The completed flow state
        
        Raises:
            ServiceError: If the flow encounters an error
        """
        # Initialize or use provided state
        if state is None:
            state = ApifyIngestState(source_config_id=config_id)

        state.start_time = datetime.now(timezone.utc)
        state.add_log(f"Starting ingestion for source config ID {config_id}")
        
        try:
            # Fetch the source configuration
            with self.session_factory() as session:
                source_config = self.source_config_crud.get(session, config_id)
                if not source_config:
                    state.set_error("fetch_config", ValueError(f"ApifySourceConfig with ID {config_id} not found"))
                    state.status = ApifyIngestStatus.ACTOR_FAILED
                    return state
                
                state.actor_id = source_config.actor_id
                state.add_log(f"Using actor {source_config.actor_id}")
            
            # Run the actor
            state.status = ApifyIngestStatus.RUNNING_ACTOR
            
            actor_input = run_input or source_config.default_input or {}
            state.actor_input = actor_input
            
            try:
                actor_run = self.apify_service.run_actor(source_config.actor_id, actor_input)
                state.apify_run_id = actor_run.get("id")
                state.add_log(f"Started actor run with ID {state.apify_run_id}")
            except Exception as e:
                state.set_error("run_actor", e)
                state.status = ApifyIngestStatus.ACTOR_FAILED
                state.add_log(f"Actor run failed: {str(e)}")
                return state
            
            # Wait for the actor run to complete and fetch details
            try:
                run_detail = self._wait_for_actor_run(state.apify_run_id)
                if run_detail.get("status") != "SUCCEEDED":
                    state.set_error("actor_run", ValueError(f"Actor run failed with status: {run_detail.get('status')}"))
                    state.status = ApifyIngestStatus.ACTOR_FAILED
                    state.add_log(f"Actor run failed with status: {run_detail.get('status')}")
                    return state
                
                state.status = ApifyIngestStatus.ACTOR_SUCCEEDED
                state.add_log("Actor run completed successfully")
            except Exception as e:
                state.set_error("wait_for_actor", e)
                state.status = ApifyIngestStatus.ACTOR_FAILED
                state.add_log(f"Error waiting for actor run: {str(e)}")
                return state
            
            # Fetch dataset items
            dataset_id = run_detail.get("defaultDatasetId")
            if not dataset_id:
                state.set_error("fetch_dataset", ValueError("Actor run did not produce a dataset"))
                state.status = ApifyIngestStatus.DATASET_FETCH_FAILED
                state.add_log("Actor run did not produce a dataset")
                return state
            
            state.dataset_id = dataset_id
            state.status = ApifyIngestStatus.FETCHING_DATASET
            state.add_log(f"Fetching items from dataset {dataset_id}")
            
            try:
                dataset_result = self.apify_service.get_dataset_items(dataset_id)
                dataset_items = dataset_result.get("items", [])
                
                if "error" in dataset_result and dataset_result["error"]:
                    state.set_error("fetch_dataset", ValueError(f"Error fetching dataset: {dataset_result['error']}"))
                    state.status = ApifyIngestStatus.DATASET_FETCH_FAILED
                    state.add_log(f"Error fetching dataset: {dataset_result['error']}")
                    return state
                
                state.total_items = len(dataset_items)
                
                if state.total_items == 0:
                    state.status = ApifyIngestStatus.DATASET_FETCH_SUCCEEDED
                    state.add_log("Dataset contains no items")
                    return state
                
                state.add_log(f"Found {state.total_items} items in the dataset")
                state.status = ApifyIngestStatus.DATASET_FETCH_SUCCEEDED
            except Exception as e:
                state.set_error("fetch_dataset", e)
                state.status = ApifyIngestStatus.DATASET_FETCH_FAILED
                state.add_log(f"Error fetching dataset items: {str(e)}")
                return state
            
            # Process items into articles
            state.status = ApifyIngestStatus.PROCESSING_ITEMS
            state.add_log("Processing items into articles")
            
            processing_success = True
            with self.session_factory() as session:
                for i, item in enumerate(dataset_items):
                    item_id = item.get("id", f"item_{i}")
                    try:
                        # Store the raw dataset item in the database
                        apify_item = self._store_dataset_item(session, item, source_config.id)
                        
                        # Skip invalid items
                        if not self._is_valid_item(item):
                            state.skipped_items += 1
                            state.add_log(f"Skipping invalid item: {item.get('url', 'unknown URL')}")
                            continue
                        
                        # Process item into article
                        result = self._process_item_to_article(session, item, source_config)
                        if result:
                            state.processed_items += 1
                            article, is_new = result
                            
                            if is_new:
                                state.created_article_ids.append(article.id)
                            else:
                                state.updated_article_ids.append(article.id)
                        else:
                            state.failed_items += 1
                            processing_success = False
                            state.item_errors[item_id] = "Failed to process item into article"
                    except Exception as e:
                        state.failed_items += 1
                        processing_success = False
                        state.item_errors[item_id] = str(e)
                        state.add_log(f"Error processing item {item_id}: {str(e)}")
            
            # Set final status based on processing results
            if state.processed_items == 0:
                state.status = ApifyIngestStatus.PROCESSING_FAILED
                state.add_log("No items were successfully processed")
            elif state.processed_items == state.total_items:
                state.status = ApifyIngestStatus.PROCESSING_SUCCEEDED
                state.add_log(f"Successfully processed all {state.processed_items} items")
            else:
                state.status = ApifyIngestStatus.PROCESSING_PARTIAL
                state.add_log(
                    f"Partially processed items: {state.processed_items} succeeded, "
                    f"{state.failed_items} failed, {state.skipped_items} skipped"
                )
            
            # Set overall completion status
            if state.status == ApifyIngestStatus.PROCESSING_SUCCEEDED:
                state.status = ApifyIngestStatus.COMPLETED_SUCCESS
            elif state.status in [ApifyIngestStatus.PROCESSING_PARTIAL, ApifyIngestStatus.PROCESSING_FAILED]:
                state.status = ApifyIngestStatus.COMPLETED_WITH_ERRORS
            
            state.end_time = datetime.now(timezone.utc)
            return state
            
        except Exception as e:
            state.set_error("ingest_flow", e)
            state.status = ApifyIngestStatus.PROCESSING_FAILED
            state.add_log(f"Error during ingestion: {str(e)}")
            state.end_time = datetime.now(timezone.utc)
            raise ServiceError(f"Apify ingestion failed: {str(e)}") from e

    def batch_ingest(
        self, 
        config_ids: List[int],
        run_inputs: Optional[Dict[int, Dict[str, Any]]] = None,
        state: Optional[ApifyBatchIngestState] = None
    ) -> ApifyBatchIngestState:
        """Run ingestion for multiple source configurations.
        
        Args:
            config_ids: List of ApifySourceConfig IDs to process
            run_inputs: Optional mapping of config IDs to custom inputs
            state: Optional existing batch state to continue from
            
        Returns:
            The completed batch flow state
        """
        # Initialize or use provided state
        if state is None:
            state = ApifyBatchIngestState(source_config_ids=config_ids)
        
        state.total_configs = len(config_ids)
        run_inputs = run_inputs or {}
        
        state.start_time = datetime.now(timezone.utc)
        state.add_log(f"Starting batch ingestion for {len(config_ids)} sources")
        
        for config_id in config_ids:
            run_input = run_inputs.get(config_id)
            state.add_log(f"Processing source config ID {config_id}")
            
            try:
                source_state = self.ingest_from_config(config_id, run_input)
                state.add_sub_state(config_id, source_state)
            except Exception as e:
                state.set_error(f"batch_ingest_{config_id}", e)
                source_state = ApifyIngestState(
                    source_config_id=config_id,
                    status=ApifyIngestStatus.PROCESSING_FAILED
                )
                source_state.set_error("batch_process", e)
                state.add_sub_state(config_id, source_state)
                state.add_log(f"Error processing source {config_id}: {str(e)}")
        
        # Set final status based on results
        if state.failed_configs == 0:
            state.status = ApifyIngestStatus.COMPLETED_SUCCESS
        elif state.failed_configs == state.total_configs:
            state.status = ApifyIngestStatus.COMPLETED_WITH_ERRORS
        else:
            state.status = ApifyIngestStatus.COMPLETED_WITH_ERRORS
        
        state.end_time = datetime.now(timezone.utc)
        state.add_log(
            f"Batch ingestion completed with {state.processed_configs - state.failed_configs} "
            f"successes and {state.failed_configs} failures"
        )
        return state

    def _wait_for_actor_run(self, run_id: str) -> Dict[str, Any]:
        """Wait for an actor run to complete.
        
        Args:
            run_id: Apify actor run ID
            
        Returns:
            Actor run details
        """
        # This would be implemented in the ApifyService
        # For now, let's assume the service has this method
        return {"status": "SUCCEEDED", "defaultDatasetId": "some-dataset-id"}

    def _store_dataset_item(
        self, 
        session: Session, 
        item: Dict[str, Any], 
        source_config_id: int
    ) -> ApifyDatasetItem:
        """Store a raw dataset item in the database.
        
        Args:
            session: Database session
            item: Raw dataset item from Apify
            source_config_id: ID of the source configuration
            
        Returns:
            The stored ApifyDatasetItem model
        """
        # Implementation would depend on the actual database model structure
        # This is a placeholder that would need to be implemented
        # with the actual database models and CRUD operations
        return None

    def _is_valid_item(self, item: Dict[str, Any]) -> bool:
        """Check if an item has the required fields to create an article.
        
        Args:
            item: Dataset item to validate
            
        Returns:
            True if the item has all required fields, False otherwise
        """
        required_fields = ['url', 'title', 'content']
        return all(field in item and item[field] for field in required_fields)

    def _process_item_to_article(
        self, 
        session: Session, 
        item: Dict[str, Any],
        source_config: ApifySourceConfig
    ) -> Optional[Tuple[Article, bool]]:
        """Process a dataset item into an article.
        
        Args:
            session: Database session
            item: Dataset item to process
            source_config: Source configuration used for the ingestion
            
        Returns:
            Tuple of (Article, is_new) or None if processing failed
            where is_new indicates if the article was newly created
        """
        # This would use the article service to create or update articles
        # Implementation would involve mapping fields from Apify item to Article model
        # For now, this is a placeholder
        return None