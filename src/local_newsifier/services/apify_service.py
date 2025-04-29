"""Service for interacting with the Apify API."""

from typing import Any, Dict, Optional

from apify_client import ApifyClient

from local_newsifier.config.settings import settings


class ApifyService:
    """Service for interacting with the Apify API."""

    def __init__(self, token: Optional[str] = None):
        """Initialize the Apify service.
        
        Args:
            token: Optional token override. If not provided, uses settings.APIFY_TOKEN
        """
        self._token = token
        self._client = None

    @property
    def client(self) -> ApifyClient:
        """Get the Apify client.
        
        Returns:
            ApifyClient: Configured Apify client
            
        Raises:
            ValueError: If APIFY_TOKEN is not set
        """
        if self._client is None:
            # Get token from settings if not provided
            token = self._token or settings.validate_apify_token()
            self._client = ApifyClient(token)
        return self._client
        
    def run_actor(self, actor_id: str, run_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run an Apify actor.
        
        Args:
            actor_id: ID of the actor to run
            run_input: Input for the actor run
            
        Returns:
            Dict[str, Any]: Actor run results
            
        Raises:
            ValueError: If APIFY_TOKEN is not set
        """
        # This will raise a clear error if token is missing via the client property
        return self.client.actor(actor_id).call(run_input=run_input)
    
    def get_dataset_items(self, dataset_id: str, **kwargs) -> Dict[str, Any]:
        """Get items from an Apify dataset.
        
        Args:
            dataset_id: ID of the dataset to get items from
            **kwargs: Additional arguments to pass to the API
            
        Returns:
            Dict[str, Any]: Dataset items in format {"items": [...]}
            
        Raises:
            ValueError: If APIFY_TOKEN is not set
        """
        list_page = self.client.dataset(dataset_id).list_items(**kwargs)
        
        # Handle different ways to access items from ListPage object
        try:
            # Try direct attribute access first
            if hasattr(list_page, 'items'):
                return {"items": list_page.items}
            # Try __iter__ for iterable objects
            elif hasattr(list_page, '__iter__'):
                return {"items": list(list_page)}
            # Try data attribute if it exists
            elif hasattr(list_page, 'data'):
                return {"items": list_page.data}
            # If it's a dictionary-like object
            elif hasattr(list_page, 'get'):
                return {"items": list_page.get('items', [])}
            # Last resort - convert to string and evaluate as JSON
            else:
                import json
                return {"items": json.loads(str(list_page))}
        except Exception as e:
            # If all else fails, return empty items list
            return {"items": [], "error": str(e)}
    
    def get_actor_details(self, actor_id: str) -> Dict[str, Any]:
        """Get details about an Apify actor.
        
        Args:
            actor_id: ID of the actor to get details for
            
        Returns:
            Dict[str, Any]: Actor details
            
        Raises:
            ValueError: If APIFY_TOKEN is not set
        """
        return self.client.actor(actor_id).get()
