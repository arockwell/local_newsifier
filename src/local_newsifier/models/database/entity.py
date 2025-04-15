"""
LEGACY MODEL - DO NOT USE

This module is deprecated and exists only for backward compatibility.
Please use the SQLModel-based Entity model instead:

from local_newsifier.models import Entity
"""

from typing import Optional, Any, Dict
from datetime import datetime


# Compatibility stub that doesn't define actual tables
class EntityDB:
    """
    Legacy model for compatibility only.
    
    IMPORTANT: This is a stub class and should not be used in new code.
    Use local_newsifier.models.Entity instead.
    """
    __tablename__ = "entities"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = None
    article_id: int = 0
    text: str = ""
    entity_type: str = ""
    confidence: float = 1.0
    sentence_context: Optional[str] = None
    created_at: datetime = datetime.now()
    
    # Stub relationship
    article: Any = None
    
    def __init__(self, **kwargs):
        """Initialize with kwargs for compatibility."""
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def model_dump(self) -> Dict[str, Any]:
        """Compatibility method."""
        return {
            "id": self.id,
            "article_id": self.article_id,
            "text": self.text,
            "entity_type": self.entity_type,
            "confidence": self.confidence,
            "sentence_context": self.sentence_context,
            "created_at": self.created_at
        }

# Keep these for compatibility
from pydantic import BaseModel

class EntityBase(BaseModel):
    """Base Pydantic model for entities. DEPRECATED."""
    text: str
    entity_type: str
    confidence: float
    sentence_context: Optional[str] = None

class EntityCreate(EntityBase):
    """Pydantic model for creating entities. DEPRECATED."""
    article_id: int

class Entity(EntityBase):
    """Pydantic model for entities with relationships. DEPRECATED."""
    id: int
    article_id: int
    
    class Config:
        """Pydantic config."""
        from_attributes = True
        
# Update forward references for compatibility
Entity.model_rebuild()