"""Async service for interacting with the Apify API."""

import logging
import os
from typing import Optional

from apify_client import ApifyClientAsync

from local_newsifier.config.settings import settings


class ApifyServiceAsync:
    """Async service for interacting with the Apify API."""

    def __init__(self, token: Optional[str] = None, test_mode: bool = False):
        """Initialize the async Apify service.

        Args:
            token: Optional token override. If not provided, uses settings.APIFY_TOKEN
            test_mode: If True, operates in test mode where token validation is skipped
        """
        self._token = token
        self._client = None
        self._test_mode = test_mode or os.environ.get("PYTEST_CURRENT_TEST") is not None

    @property
    def client(self) -> ApifyClientAsync:
        """Get the async Apify client.

        Returns:
            ApifyClientAsync: Configured async Apify client

        Raises:
            ValueError: If APIFY_TOKEN is not set and not in test mode
        """
        if self._client is None:
            # For test mode, use a dummy token if not provided
            if self._test_mode and not self._token and not settings.APIFY_TOKEN:
                logging.warning("Running in test mode with dummy APIFY_TOKEN")
                token = "test_dummy_token"
            else:
                # Get token from settings if not provided
                token = self._token or settings.validate_apify_token()

            self._client = ApifyClientAsync(token)

        return self._client

    async def close(self):
        """Close the async client."""
        if self._client:
            await self._client.aclose()
