"""
HTTP Client for CLI commands to communicate with FastAPI backend.

This client provides a clean interface for CLI commands to communicate with
the FastAPI backend, eliminating event loop conflicts and direct dependency injection.
"""

import os
from typing import Any, Dict, List, Optional

import httpx
from httpx import ConnectError, HTTPStatusError, TimeoutException


class NewsifierAPIError(Exception):
    """Custom exception for API errors."""

    def __init__(self, status_code: int, detail: str):
        """Initialize the API error with status code and detail."""
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error ({status_code}): {detail}")


class NewsifierClient:
    """Synchronous HTTP client for Local Newsifier API."""

    def __init__(
        self, base_url: Optional[str] = None, timeout: float = 30.0, local_mode: bool = False
    ):
        """Initialize the client.

        Args:
            base_url: Base URL for the API. Defaults to env var or localhost.
            timeout: Request timeout in seconds.
            local_mode: If True, use TestClient for local testing (not implemented yet).
        """
        self.base_url = base_url or os.getenv("NEWSIFIER_API_URL", "http://localhost:8000")
        self.timeout = timeout
        self.local_mode = local_mode
        self._client = None

    def __enter__(self):
        """Context manager entry."""
        self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._client:
            self._client.close()

    @property
    def client(self) -> httpx.Client:
        """Get the HTTP client, creating one if needed."""
        if not self._client:
            self._client = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        return self._client

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise exceptions for errors."""
        try:
            response.raise_for_status()
            return response.json()
        except HTTPStatusError as e:
            # Try to extract error detail from response
            try:
                error_detail = e.response.json().get("detail", str(e))
            except Exception:
                error_detail = str(e)
            raise NewsifierAPIError(e.response.status_code, error_detail)
        except Exception as e:
            # Handle other errors
            raise NewsifierAPIError(500, str(e))

    # Database commands

    def get_db_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        response = self.client.get("/db/stats")
        return self._handle_response(response)

    def get_duplicates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get duplicate articles."""
        response = self.client.get("/db/duplicates", params={"limit": limit})
        return self._handle_response(response)

    def list_articles(
        self,
        source: Optional[str] = None,
        status: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """List articles with filtering options."""
        params = {"limit": limit}
        if source:
            params["source"] = source
        if status:
            params["status"] = status
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        response = self.client.get("/db/articles", params=params)
        return self._handle_response(response)

    def inspect_record(self, table: str, id: int) -> Dict[str, Any]:
        """Inspect a specific database record."""
        response = self.client.get(f"/db/inspect/{table}/{id}")
        return self._handle_response(response)

    def purge_duplicates(self, dry_run: bool = True) -> Dict[str, Any]:
        """Remove duplicate articles."""
        response = self.client.post("/db/purge-duplicates", json={"dry_run": dry_run})
        return self._handle_response(response)

    # RSS Feed commands

    def list_feeds(
        self, active_only: bool = False, limit: int = 100, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """List RSS feeds."""
        params = {"limit": limit, "skip": skip, "active_only": active_only}
        response = self.client.get("/feeds", params=params)
        return self._handle_response(response)

    def get_feed(self, feed_id: int) -> Dict[str, Any]:
        """Get a specific RSS feed."""
        response = self.client.get(f"/feeds/{feed_id}")
        return self._handle_response(response)

    def add_feed(
        self, url: str, name: Optional[str] = None, description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a new RSS feed."""
        data = {"url": url}
        if name:
            data["name"] = name
        if description:
            data["description"] = description

        response = self.client.post("/feeds", json=data)
        return self._handle_response(response)

    def update_feed(
        self,
        feed_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update an RSS feed."""
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if is_active is not None:
            data["is_active"] = is_active

        response = self.client.patch(f"/feeds/{feed_id}", json=data)
        return self._handle_response(response)

    def delete_feed(self, feed_id: int) -> Dict[str, Any]:
        """Delete an RSS feed."""
        response = self.client.delete(f"/feeds/{feed_id}")
        return self._handle_response(response)

    def process_feed(self, feed_id: int) -> Dict[str, Any]:
        """Process a specific RSS feed."""
        response = self.client.post(f"/feeds/{feed_id}/process")
        return self._handle_response(response)

    def process_all_feeds(self) -> Dict[str, Any]:
        """Process all active RSS feeds."""
        response = self.client.post("/feeds/process-all")
        return self._handle_response(response)

    # Health check

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        try:
            response = self.client.get("/health")
            return self._handle_response(response)
        except ConnectError:
            raise NewsifierAPIError(503, "Cannot connect to API server")
        except TimeoutException:
            raise NewsifierAPIError(504, "Request timed out")
