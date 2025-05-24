"""FastAPI middleware for Prometheus metrics collection."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .metrics import api_active_requests, api_request_counter, api_request_duration


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to track API requests with Prometheus metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Extract endpoint and method
        method = request.method
        endpoint = self._get_endpoint_pattern(request)

        # Track active requests
        api_active_requests.labels(method=method, endpoint=endpoint).inc()

        # Time the request
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            api_request_counter.labels(
                method=method, endpoint=endpoint, status_code=response.status_code
            ).inc()

            api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record error metrics
            api_request_counter.labels(method=method, endpoint=endpoint, status_code=500).inc()

            api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

            raise e

        finally:
            # Decrement active requests
            api_active_requests.labels(method=method, endpoint=endpoint).dec()

    def _get_endpoint_pattern(self, request: Request) -> str:
        """Extract endpoint pattern from request."""
        # Get the matched route if available
        if hasattr(request, "scope") and "route" in request.scope:
            route = request.scope["route"]
            if hasattr(route, "path"):
                return route.path

        # Fallback to URL path
        path = request.url.path

        # Normalize common patterns
        # Replace IDs with placeholders
        import re

        # UUID pattern
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/{id}", path
        )

        # Numeric ID pattern
        path = re.sub(r"/\d+", "/{id}", path)

        return path
