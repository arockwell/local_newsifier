"""Base DTO classes for common response patterns."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, Generic, List, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

T = TypeVar('T')


class ProcessingStatus(str, Enum):
    """Standard processing status for operations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class BaseOperationResultDTO(BaseModel):
    """Base class for operation results with success/failure tracking."""
    
    success: bool = True
    status: ProcessingStatus = ProcessingStatus.COMPLETED
    error_message: Optional[str] = None
    operation_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "status": "completed",
                    "error_message": None,
                    "operation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2023-01-01T12:00:00Z"
                }
            ]
        }
    }


class BaseListResultDTO(BaseModel, Generic[T]):
    """Base class for paginated list responses."""
    
    items: List[T]
    total: int
    page: int = 1
    size: int = 50
    has_next: bool = False
    has_prev: bool = False
    
    # Operation metadata
    success: bool = True
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-calculate pagination flags
        if 'has_next' not in data:
            self.has_next = (self.page * self.size) < self.total
        if 'has_prev' not in data:
            self.has_prev = self.page > 1
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "items": [],
                    "total": 100,
                    "page": 1,
                    "size": 50,
                    "has_next": True,
                    "has_prev": False,
                    "success": True,
                    "timestamp": "2023-01-01T12:00:00Z"
                }
            ]
        }
    }


class ErrorResponseDTO(BaseModel):
    """Standardized error response for API and service errors."""
    
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Common error codes
    VALIDATION_ERROR: ClassVar[str] = "VALIDATION_ERROR"
    NOT_FOUND: ClassVar[str] = "NOT_FOUND"
    INTERNAL_ERROR: ClassVar[str] = "INTERNAL_ERROR"
    EXTERNAL_API_ERROR: ClassVar[str] = "EXTERNAL_API_ERROR"
    PROCESSING_ERROR: ClassVar[str] = "PROCESSING_ERROR"
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error_code": "VALIDATION_ERROR",
                    "message": "Invalid input parameters",
                    "details": {"field": "url", "issue": "Invalid URL format"},
                    "request_id": "req-123456",
                    "timestamp": "2023-01-01T12:00:00Z"
                }
            ]
        }
    }


class MetadataDTO(BaseModel):
    """Common metadata fields for operation results."""
    
    processing_duration_ms: Optional[int] = None
    source: Optional[str] = None
    version: str = "1.0"
    additional_info: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "processing_duration_ms": 1500,
                    "source": "analysis_service",
                    "version": "1.0",
                    "additional_info": {"algorithm": "spacy_nlp"}
                }
            ]
        }
    }