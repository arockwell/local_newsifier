"""FastAPI middleware for performance monitoring."""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from local_newsifier.monitoring.metrics import (api_active_requests, api_request_duration,
                                                api_request_total)

logger = logging.getLogger(__name__)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to track API request metrics."""

    def __init__(self, app: ASGIApp, app_name: str = "newsifier"):
        super().__init__(app)
        self.app_name = app_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track metrics.

        Args:
            request: FastAPI request object
            call_next: Next middleware in chain

        Returns:
            Response object
        """
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Track active requests
        api_active_requests.inc()

        # Start timing
        start_time = time.time()

        # Default values
        method = request.method
        endpoint = request.url.path
        status_code = 500

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            return response

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Update metrics
            api_active_requests.dec()

            # Convert status code to status group (2xx, 3xx, 4xx, 5xx)
            status_group = f"{status_code // 100}xx"

            # Record metrics with labels
            labels = {
                "method": method,
                "endpoint": self._normalize_endpoint(endpoint),
                "status": status_group,
            }

            api_request_duration.labels(**labels).observe(duration)
            api_request_total.labels(**labels).inc()

            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {method} {endpoint} took {duration:.2f}s "
                    f"(status: {status_code})"
                )

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for consistent metrics.

        Replaces dynamic path parameters with placeholders.

        Args:
            path: URL path

        Returns:
            Normalized path
        """
        # Common patterns to normalize
        import re

        # Replace UUIDs first (more specific pattern)
        path = re.sub(
            r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            "/{uuid}",
            path,
        )

        # Then replace numeric IDs (less specific pattern)
        path = re.sub(r"/\d+", "/{id}", path)

        # Limit path segments to avoid high cardinality
        segments = path.split("/")
        if len(segments) > 5:
            path = "/".join(segments[:5]) + "/..."

        return path
