"""
LEGACY MODEL - DO NOT USE

This module is deprecated and exists only for backward compatibility.
Please use the SQLModel-based AnalysisResult model instead:

from local_newsifier.models import AnalysisResult
"""

from typing import Dict, Any, Optional
from datetime import datetime


# Compatibility stub that doesn't define actual tables
class AnalysisResultDB:
    """
    Legacy model for compatibility only.
    
    IMPORTANT: This is a stub class and should not be used in new code.
    Use local_newsifier.models.AnalysisResult instead.
    """
    __tablename__ = "analysis_results"
    __table_args__ = {'extend_existing': True}
    
    id: Optional[int] = None
    article_id: int = 0
    analysis_type: str = ""
    results: Dict[str, Any] = {}
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
            "analysis_type": self.analysis_type,
            "results": self.results,
            "created_at": self.created_at
        }