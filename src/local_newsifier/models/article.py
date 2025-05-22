"""Article model for the news analysis system."""

from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.entity import Entity
    from local_newsifier.models.analysis_result import AnalysisResult


class ArticleBase(SQLModel):
    """Base model for Article."""
    # TODO: move field definitions from Article here

class ArticleRead(ArticleBase):
    """Read model for Article."""
    pass

class Article(ArticleBase, table=True):
    """SQLModel for articles - serves as both ORM model and Pydantic schema."""

    __tablename__ = "articles"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}
    
    # Primary key and timestamps
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )
    
    # Article fields
    title: str
    content: str
    url: str = Field(unique=True)
    source: str
    published_at: datetime
    status: str
    scraped_at: datetime
    
    # Define relationships with fully qualified paths
    entities: List["local_newsifier.models.entity.Entity"] = Relationship(back_populates="article")
    analysis_results: List["local_newsifier.models.analysis_result.AnalysisResult"] = Relationship(back_populates="article")
    
    # Model configuration for both SQLModel and Pydantic functionality
    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Sample Article",
                    "content": "This is a sample article content.",
                    "url": "https://example.com/sample",
                    "source": "Example News",
                    "published_at": "2023-01-01T00:00:00Z",
                    "status": "new",
                    "scraped_at": "2023-01-01T01:00:00Z",
                }
            ]
        }
    }
