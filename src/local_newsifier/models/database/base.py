"""
LEGACY BASE MODEL - DO NOT USE

This module is deprecated and exists only for backward compatibility.
Please use the SQLModel-based models instead:

from local_newsifier.models import Article, Entity, AnalysisResult
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type


# Compatibility stub
class Base:
    """
    Legacy base model for compatibility only.
    
    IMPORTANT: This is a stub class and should not be used in new code.
    Use SQLModel-based models instead.
    """
    __tablename__: str = ""
    id: Optional[int] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    
    # Add compatibility methods
    def model_dump(self) -> Dict[str, Any]:
        """Compatibility method."""
        attributes = self.__dict__.copy()
        if "_sa_instance_state" in attributes:
            del attributes["_sa_instance_state"]
        return attributes
    
    @classmethod
    def metadata(cls) -> Any:
        """Dummy metadata that doesn't define tables."""
        class DummyMetadata:
            def create_all(self, *args, **kwargs):
                pass
        return DummyMetadata()