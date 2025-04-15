"""
LEGACY MODEL - DO NOT USE

This module is deprecated and exists only for backward compatibility.
Please use the SQLModel-based Article model instead:

from local_newsifier.models import Article
"""

from typing import List, Optional, Any, Dict
from datetime import datetime


# Compatibility stub that doesn't define actual tables
class ArticleDB:
    """
    Legacy model for compatibility only.
    
    IMPORTANT: This is a stub class and should not be used in new code.
    Use local_newsifier.models.Article instead.
    """
    __tablename__ = "articles"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = None
    title: str = ""
    content: str = ""
    url: str = ""
    source: str = ""
    published_at: datetime = datetime.now()
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    status: str = ""
    scraped_at: datetime = datetime.now()
    
    # Stub relationships
    entities: List[Any] = []
    analysis_results: List[Any] = []
    
    def __init__(self, **kwargs):
        """Initialize with kwargs for compatibility."""
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def model_dump(self) -> Dict[str, Any]:
        """Compatibility method."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "scraped_at": self.scraped_at
        }