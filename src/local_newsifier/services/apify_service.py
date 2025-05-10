"""Service for interacting with Apify API."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable

from fastapi_injectable import injectable
from typing import Annotated
from fastapi import Depends

from local_newsifier.config.settings import settings
from local_newsifier.errors import handle_apify


@injectable(use_cache=False)
class ApifyService:
    """Service for Apify API operations."""

    def __init__(self, token: Optional[str] = None, test_mode: bool = False):
        """Initialize the Apify service.
        
        Args:
            token: API token for Apify authentication. If not provided, the token from
                  settings.APIFY_TOKEN will be used.
            test_mode: If True, operate in test mode with mock responses when no token
        """
        self._token = token
        self._client = None
        self._test_mode = test_mode or settings.TEST_MODE
        
    @property
    def client(self):
        """Get the Apify client.
        
        Returns:
            ApifyClient: Initialized Apify client
            
        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        if self._client is None:
            # Try to use the provided token, fallback to settings
            token = self._token or settings.APIFY_TOKEN
            
            # Only raise if we're not in test mode
            if not token and not self._test_mode:
                raise ValueError("APIFY_TOKEN is not set. Please set the APIFY_TOKEN environment "
                                "variable or pass a token to ApifyService.")
                
            # Import at runtime to avoid dependency for tests
            try:
                from apify_client import ApifyClient
                self._client = ApifyClient(token)
            except ImportError:
                # Make the import error more helpful
                raise ImportError("The 'apify_client' package is required. "
                                "Please install it with 'pip install apify-client'.")
        return self._client

    @handle_apify
    def run_actor(self, actor_id: str, run_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run an Apify actor.
        
        Args:
            actor_id: ID of the actor to run
            run_input: Optional input for the actor run
            
        Returns:
            Dict[str, Any]: Actor run results

        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        # In test mode with no token, return a mock response
        if self._test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating run of actor {actor_id}")
            return {
                "id": f"test_run_{actor_id}",
                "actId": actor_id,
                "status": "SUCCEEDED",
                "defaultDatasetId": f"test_dataset_{actor_id}",
                "defaultKeyValueStoreId": f"test_store_{actor_id}",
            }
            
        # Make the actual API call
        return self.client.actor(actor_id).call(run_input=run_input)
    
    def create_schedule(
        self, 
        actor_id: str, 
        cron_expression: str, 
        run_input: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a schedule for an actor in Apify.
        
        Args:
            actor_id: ID of the actor to schedule
            cron_expression: Cron expression for the schedule (in UTC)
            run_input: Optional input for the actor run
            name: Optional name for the schedule
            
        Returns:
            Dict[str, Any]: Created schedule details
            
        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        # In test mode with no token, return a mock response
        if self._test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating schedule creation for actor {actor_id}")
            schedule_id = f"test_schedule_{actor_id}_{datetime.now(timezone.utc).timestamp()}"
            # Create a mock response that includes the actions field for test compatibility
            mock_response = {
                "id": schedule_id,
                "name": name or f"Schedule for {actor_id}",
                "userId": "test_user",
                "actId": actor_id,
                "cronExpression": cron_expression,
                "isEnabled": True,
                "isExclusive": False,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "modifiedAt": datetime.now(timezone.utc).isoformat(),
                "actions": [{
                    "type": "RUN_ACTOR",
                    "actorId": actor_id
                }]
            }
            # Add input to actions if provided
            if run_input:
                mock_response["actions"][0]["input"] = run_input
                
            return mock_response
        
        # Create actions for the schedule (requires the actor to run)
        actions = [{
            "type": "RUN_ACTOR",
            "actorId": actor_id
        }]
        
        # Add input if provided
        if run_input:
            actions[0]["input"] = run_input
            
        # Format name to match Apify requirements (alphanumeric with hyphens only in middle)
        default_name = f"localnewsifier-{actor_id.replace('/', '-')}"
        # Ensure the name follows the required format
        sanitized_name = name or default_name
        sanitized_name = sanitized_name.lower().replace('_', '-')
        # Remove any characters that aren't allowed
        import re
        sanitized_name = re.sub(r'[^a-z0-9-]', '', sanitized_name)
        # Ensure hyphens aren't at start or end
        sanitized_name = sanitized_name.strip('-')
        # If the name is all gone, use a default
        if not sanitized_name:
            sanitized_name = "localnewsifier"
            
        # Prepare schedule parameters according to API requirements
        schedule_params = {
            "name": sanitized_name,
            "cron_expression": cron_expression,
            "is_enabled": True,
            "is_exclusive": True,  # Don't start if previous run is still going
            "actions": actions,
            "timezone": "UTC"
        }
            
        # Make the actual API call
        schedules_client = self.client.schedules()
        return schedules_client.create(**schedule_params)
        
    def update_schedule(self, schedule_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing Apify schedule.
        
        Args:
            schedule_id: ID of the schedule to update
            changes: Dictionary of changes to apply to the schedule
            
        Returns:
            Dict[str, Any]: Updated schedule details
            
        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        # In test mode with no token, return a mock response
        if self._test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating schedule update for {schedule_id}")
            return {
                "id": schedule_id,
                "name": changes.get("name", f"Schedule {schedule_id}"),
                "userId": "test_user",
                "actId": changes.get("actId", "test_actor"),
                "cronExpression": changes.get("cronExpression", "0 0 * * *"),
                "isEnabled": changes.get("isEnabled", True),
                "isExclusive": changes.get("isExclusive", False),
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "modifiedAt": datetime.now(timezone.utc).isoformat(),
            }
        
        # Make the actual API call
        # Convert parameter names to match API expectations
        # The Apify API uses snake_case for parameters, but our code uses camelCase
        converted_changes = {}

        # Handle parameter name conversions
        param_mapping = {
            "cronExpression": "cron_expression",
            "isEnabled": "is_enabled",
            "isExclusive": "is_exclusive",
        }

        # Skip parameters that aren't supported by the Apify API
        unsupported_params = ["actId", "runInput"]

        for key, value in changes.items():
            # Skip unsupported parameters
            if key in unsupported_params:
                continue

            # Convert camelCase to snake_case if needed
            api_key = param_mapping.get(key, key)
            converted_changes[api_key] = value

        # Pass converted changes as keyword arguments
        return self.client.schedule(schedule_id).update(**converted_changes)
        
    def delete_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Delete an Apify schedule.
        
        Args:
            schedule_id: ID of the schedule to delete
            
        Returns:
            Dict[str, Any]: Deleted schedule details
            
        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        # In test mode with no token, return a mock response
        if self._test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating schedule deletion for {schedule_id}")
            return {
                "id": schedule_id,
                "name": f"Schedule {schedule_id}",
                "userId": "test_user",
                "actId": "test_actor",
                "cronExpression": "0 0 * * *",
                "isEnabled": False,
                "isExclusive": False,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "modifiedAt": datetime.now(timezone.utc).isoformat(),
            }
        
        # Make the actual API call
        schedule = self.client.schedule(schedule_id)
        deletion_result = schedule.delete()
        return {"id": schedule_id, "deleted": deletion_result}
        
    def get_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Get details about a specific Apify schedule.
        
        Args:
            schedule_id: ID of the schedule to get
            
        Returns:
            Dict[str, Any]: Schedule details
            
        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        # In test mode with no token, return a mock response
        if self._test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating schedule details fetch for {schedule_id}")
            return {
                "id": schedule_id,
                "name": f"Schedule {schedule_id}",
                "userId": "test_user",
                "actId": "test_actor",
                "cronExpression": "0 0 * * *",
                "isEnabled": True,
                "isExclusive": False,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "modifiedAt": datetime.now(timezone.utc).isoformat(),
            }
        
        # Make the actual API call
        return self.client.schedule(schedule_id).get()
        
    def list_schedules(self, actor_id: Optional[str] = None) -> Dict[str, Any]:
        """List all schedules or those for a specific actor.
        
        Args:
            actor_id: Optional actor ID to filter schedules by
            
        Returns:
            Dict[str, Any]: Dictionary containing a list of schedules
            
        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        # In test mode with no token, return a mock response
        if self._test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating schedule list fetch")
            schedules = []
            if actor_id:
                schedules.append({
                    "id": f"test_schedule_{actor_id}",
                    "name": f"Schedule for {actor_id}",
                    "userId": "test_user",
                    "actId": actor_id,
                    "cronExpression": "0 0 * * *",
                    "isEnabled": True,
                    "isExclusive": False,
                    "createdAt": datetime.now(timezone.utc).isoformat(),
                    "modifiedAt": datetime.now(timezone.utc).isoformat(),
                })
            else:
                # Add a couple of mock schedules
                for i in range(1, 3):
                    schedules.append({
                        "id": f"test_schedule_{i}",
                        "name": f"Test Schedule {i}",
                        "userId": "test_user",
                        "actId": f"test_actor_{i}",
                        "cronExpression": "0 0 * * *",
                        "isEnabled": True,
                        "isExclusive": False,
                        "createdAt": datetime.now(timezone.utc).isoformat(),
                        "modifiedAt": datetime.now(timezone.utc).isoformat(),
                    })
            return {"data": {"items": schedules, "total": len(schedules)}}
        
        # Prepare filter parameters if needed
        filter_by = None
        if actor_id:
            # Note: The Apify API has a different structure for list filtering
            # which we'll need to check in their documentation
            filter_by = {"actorId": actor_id}
            
        # Make the actual API call
        schedules_client = self.client.schedules()
        return schedules_client.list(filter_by=filter_by)

    def _format_error(self, error: Exception, context: str = "") -> str:
        """Format an error with traceback and context.
        
        Args:
            error: The exception to format
            context: Optional context for the error
            
        Returns:
            str: Formatted error message with traceback and context
        """
        import traceback
        stack_trace = traceback.format_exc()
        context_info = f" during {context}" if context else ""
        return f"Error{context_info}: {str(error)}\n{stack_trace}"
    
    @handle_apify
    def get_dataset_items(
        self, dataset_id: str, **kwargs
    ) -> Dict[str, Any]:
        """Get items from a dataset.
        
        Args:
            dataset_id: ID of the dataset to get items from
            **kwargs: Additional parameters to pass to the list_items method
            
        Returns:
            Dict[str, Any]: Dataset items in format {"items": [...], "error": "..."}

        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        # In test mode with no token, return mock data
        if self._test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating dataset items for {dataset_id}")
            return {
                "items": [
                    {
                        "id": 1,
                        "url": "https://example.com/test",
                        "title": "Test Article",
                        "content": "This is test content for testing without a real Apify token."
                    }
                ]
            }
            
        # Handle API call exceptions gracefully
        try:
            list_page = self.client.dataset(dataset_id).list_items(**kwargs)
            return {"items": list_page["items"]}
        except Exception as e:
            error_message = self._format_error(e, context=f"retrieving dataset {dataset_id}")
            return {"items": [], "error": error_message}
    
    @handle_apify
    def get_actor_details(self, actor_id: str) -> Dict[str, Any]:
        """Get details about an actor.
        
        Args:
            actor_id: ID of the actor to get details for
            
        Returns:
            Dict[str, Any]: Actor details

        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        # In test mode with no token, return mock data
        if self._test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating actor details for {actor_id}")
            return {
                "id": actor_id,
                "name": f"test_{actor_id}",
                "title": f"Test Actor: {actor_id}",
                "description": "This is a mock actor for testing without a real Apify token.",
                "version": {"versionNumber": "1.0.0"},
                "defaultRunInput": {"field1": "value1"},
            }
            
        return self.client.actor(actor_id).get()