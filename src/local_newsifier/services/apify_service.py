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

        # Handle different response formats from the Apify API

        # Case 1: Already in correct format with "items" key (used in test mock)
        if isinstance(list_page, dict) and "items" in list_page:
            return list_page

        # Case 2: Handle ListPage object various ways
        try:
            # Try direct attribute access first (most common case)
            if hasattr(list_page, "items") and list_page.items is not None:
                items = list_page.items
                # Handle non-list items attribute (could be a property or method)
                if callable(items):
                    items = items()
                return {"items": items}

            # Try __iter__ for iterable objects, but check if it's safe to iterate
            elif hasattr(list_page, "__iter__") and not isinstance(
                list_page, (str, bytes)
            ):
                try:
                    # First try a safe way to convert to list to avoid consuming an iterator
                    import copy

                    items_copy = copy.copy(list_page)
                    return {"items": list(items_copy)}
                except (TypeError, ValueError):
                    # If copy fails, try direct iteration
                    return {"items": list(list_page)}

            # Try dict-like access if the object supports it
            elif hasattr(list_page, "get") and callable(list_page.get):
                try:
                    # Enhanced check: verify if it's a true dict-like object by checking
                    # for common mapping protocol methods
                    is_mapping_like = hasattr(list_page, "__getitem__") and (
                        hasattr(list_page, "keys") or hasattr(list_page, "__contains__")
                    )

                    # Try to inspect the signature of get() to verify it accepts arguments
                    accepts_args = False
                    try:
                        import inspect

                        sig = inspect.signature(list_page.get)
                        # Count required parameters (excluding self for instance methods)
                        min_args = sum(
                            1
                            for p in sig.parameters.values()
                            if p.default == inspect.Parameter.empty and
                            p.kind not in (
                                inspect.Parameter.VAR_POSITIONAL,
                                inspect.Parameter.VAR_KEYWORD,
                            )
                        )

                        # Subtract 'self' parameter for bound methods
                        if hasattr(list_page.get, "__self__"):
                            min_args = max(0, min_args - 1)

                        accepts_args = (
                            min_args <= 1
                        )  # Should accept at most one required arg
                    except (TypeError, ValueError):
                        # If we can't inspect the signature, we'll rely on the is_mapping_like check
                        pass

                    # Only try to call get() if it's likely to work
                    if is_mapping_like or accepts_args:
                        # Try various common key names used by different APIs
                        for key in ["items", "data", "results", "content"]:
                            try:
                                items = list_page.get(key)
                                if items is not None:
                                    return {"items": items}
                            except Exception as e:
                                import logging

                                logging.debug(f"Exception when accessing get('{key}'): {str(e)}")
                                # Continue to next key
                except TypeError as e:
                    # Specifically catch TypeError which happens when get() doesn't accept a string argument
                    # Log and continue to other methods
                    import logging

                    logging.debug(f"TypeError when calling get() method: {str(e)}")
                except Exception as e:
                    # Catch any other exceptions from the get() call and continue to other methods
                    import logging

                    logging.debug(f"Error when using get() method: {str(e)}")

            # Try data attribute if it exists
            elif hasattr(list_page, "data") and list_page.data is not None:
                return {"items": list_page.data}

            # Try items attribute directly (common in many APIs and our test cases)
            elif hasattr(list_page, "items") and list_page.items is not None:
                # This case is already handled above, but we add it here as a fallback
                # in case the earlier check is skipped due to the control flow
                items = list_page.items
                # Handle non-list items attribute (could be a property or method)
                if callable(items):
                    items = items()
                return {"items": items}

            # Try accessing an "_items" private attribute (common in some APIs)
            elif hasattr(list_page, "_items") and list_page._items is not None:
                return {"items": list_page._items}

            # Last resort - convert to string and evaluate as JSON
            else:
                import json

                try:
                    # Try parsing as a JSON array directly
                    items_json = str(list_page)
                    # Strip leading/trailing whitespace that might cause JSON parsing errors
                    items_json = items_json.strip()

                    # Handle case where string doesn't start with [ or {
                    if not (items_json.startswith("[") or items_json.startswith("{")):
                        raise ValueError("Invalid JSON format")

                    parsed_data = json.loads(items_json)

                    # Handle both array and object with items field
                    if isinstance(parsed_data, list):
                        return {"items": parsed_data}
                    elif isinstance(parsed_data, dict) and "items" in parsed_data:
                        return parsed_data
                    else:
                        return {"items": [parsed_data]}
                except json.JSONDecodeError as json_err:
                    # More specific error for JSON parsing issues
                    raise ValueError(f"Failed to parse ListPage as JSON: {json_err}")
        except Exception as e:
            # If all else fails, try directly accessing attributes without property wrappers
            # Check all attributes for anything that looks like an item list
            try:
                # Iterate through all attributes of the object
                for attr_name in dir(list_page):
                    # Skip private attributes and methods
                    if attr_name.startswith("_") and attr_name != "_items":
                        continue

                    # Skip methods and built-in attributes
                    if callable(getattr(list_page, attr_name, None)) or attr_name in (
                        "__dict__",
                        "__class__",
                    ):
                        continue

                    # Try to get the attribute
                    try:
                        attr_value = getattr(list_page, attr_name)
                        # If it's a list-like object, return it as items
                        if isinstance(attr_value, (list, tuple)) and attr_value:
                            return {"items": attr_value}
                    except Exception:
                        # Skip attributes that raise exceptions
                        continue
            except Exception:
                # If direct attribute inspection fails, continue to fallback
                pass

            # Last resort fallback: empty items with error
            import traceback

            error_message = str(e)
            error_type = f"Type: {type(list_page)}"
            error_trace = f"Traceback: {traceback.format_exc()}"
            error_details = f"{error_message}\n{error_type}\n{error_trace}"
            return {"items": [], "error": error_details}

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
