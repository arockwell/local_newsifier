"""
Core error structure for external service integrations.

This module defines the ServiceError class, which provides a flexible,
consistent approach to handling errors from external services.
"""

from datetime import datetime
from typing import Any, Dict, Optional, Type
import json

class ServiceError(Exception):
    """Base error for all external service interactions.
    
    This class provides a standardized way to represent errors from 
    external services, including context preservation, error categorization,
    and metadata for debugging and error handling.
    
    Attributes:
        service (str): The service identifier (e.g., "apify", "rss").
        error_type (str): The type of error (e.g., "network", "timeout").
        message (str): Human-readable error message.
        original (Exception, optional): The original exception that was caught.
        context (Dict[str, Any], optional): Additional context information.
        is_transient (bool): Whether the error is likely temporary and can be retried.
        timestamp (datetime): When the error occurred.
    """
    
    def __init__(
        self, 
        service: str,
        error_type: str, 
        message: str, 
        original: Optional[Exception] = None, 
        context: Optional[Dict[str, Any]] = None,
        is_transient: bool = False
    ) -> None:
        """Initialize a ServiceError.
        
        Args:
            service: Identifier for the service (e.g., "apify", "rss").
            error_type: Type of error (e.g., "network", "timeout").
            message: Human-readable error message.
            original: Original exception, if any.
            context: Additional context (e.g., function args, operation details).
            is_transient: Whether this error is likely temporary and retryable.
        """
        self.service = service  # "apify", "rss", etc.
        self.error_type = error_type  # "network", "timeout", "parse", etc.  
        self.original = original  # Original exception
        self.context = context or {}
        self.timestamp = datetime.now()
        self.is_transient = is_transient  # Flag for retry logic
        
        # Format the full message
        full_message = f"{service}.{error_type}: {message}"
        super().__init__(full_message)
        
    @property
    def full_type(self) -> str:
        """Return the full error type identifier (service.type).
        
        Returns:
            str: The service and error type joined (e.g., "apify.network").
        """
        return f"{self.service}.{self.error_type}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to a dictionary for logging or serialization.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the error.
        """
        result = {
            "service": self.service,
            "error_type": self.error_type,
            "full_type": self.full_type,
            "message": str(self),
            "timestamp": self.timestamp.isoformat(),
            "is_transient": self.is_transient,
            "context": self.context,
            "original_error": str(self.original) if self.original else None,
            "original_type": type(self.original).__name__ if self.original else None
        }
            
        return result
    
    def __str__(self) -> str:
        """Return a string representation of the error.
        
        Returns:
            str: String representation of the error.
        """
        return super().__str__()
    
    def __repr__(self) -> str:
        """Return a developer representation of the error.
        
        Returns:
            str: Developer representation of the error.
        """
        return (
            f"ServiceError(service='{self.service}', "
            f"error_type='{self.error_type}', "
            f"message='{super().__str__()}', "
            f"is_transient={self.is_transient})"
        )