from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    """Details about an error that occurred during processing."""

    task: str
    type: str
    message: str
    traceback_snippet: Optional[str] = None


def extract_error_details(error: Exception) -> tuple[str, str, str | None]:
    """Extract error details from an exception, unwrapping ServiceError if needed."""
    if hasattr(error, "original") and getattr(error, "original"):
        original = error.original
        error_type = original.__class__.__name__
        message = str(original)
        traceback_snippet = str(original.__traceback__)
    else:
        error_type = error.__class__.__name__
        message = str(error)
        traceback_snippet = str(error.__traceback__)
    return error_type, message, traceback_snippet


class BaseState(BaseModel):
    """Base state model with shared fields and helpers."""

    run_id: UUID = Field(default_factory=uuid4)
    status: Enum
    error_details: Optional[ErrorDetails] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    run_logs: List[str] = Field(default_factory=list)

    # Optional class attribute for subclasses that set a failure status
    failure_status: Optional[Enum] = None

    def touch(self) -> None:
        """Update the last_updated timestamp."""
        self.last_updated = datetime.now(timezone.utc)

    def add_log(self, message: str) -> None:
        """Add a log message with timestamp."""
        timestamp = datetime.now(timezone.utc).isoformat()
        self.run_logs.append(f"[{timestamp}] {message}")
        self.touch()

    def set_error(self, task: str, error: Exception) -> None:
        """Set error details and optionally update status."""
        error_type, message, traceback_snippet = extract_error_details(error)
        self.error_details = ErrorDetails(
            task=task,
            type=error_type,
            message=message,
            traceback_snippet=traceback_snippet,
        )
        if self.failure_status is not None:
            self.status = self.failure_status
        self.touch()
