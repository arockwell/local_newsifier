"""Analysis result models for the news analysis system."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlmodel import JSON, Field, Relationship

from local_newsifier.models.base import TableBase

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.article import Article


class AnalysisResult(TableBase, table=True):
    """SQLModel for analysis results."""

    __tablename__ = "analysis_results"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    article_id: int = Field(foreign_key="articles.id")
    analysis_type: str
    results: Dict[str, Any] = Field(sa_type=JSON)
    
    # Define relationship with fully qualified path
    article: Optional["local_newsifier.models.article.Article"] = Relationship(back_populates="analysis_results")


class AnalysisResultRead(TableBase):
    """Read DTO for AnalysisResult model - used for API responses."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    article_id: int
    analysis_type: str
    results: Dict[str, Any]
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "article_id": 1,
                    "analysis_type": "sentiment",
                    "results": {
                        "sentiment_score": 0.75,
                        "confidence": 0.95,
                        "categories": ["positive", "news"]
                    },
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
    }
