"""Base database model with common fields for all models using SQLModel."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


# Configure SQLModel settings
class BaseConfig(SQLModel.Config):
    """Base configuration for all SQLModels."""
    arbitrary_types_allowed = True
    orm_mode = True
    

# Base class for table models
class TableBase(SQLModel, table=True):
    """Base model for all database tables with a primary key."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": datetime.now(timezone.utc)}
    )
    
    class Config(BaseConfig):
        """SQLModel configuration."""
        pass


# For non-table schema classes
class SchemaBase(SQLModel):
    """Base model for non-table schema classes."""
    
    class Config(BaseConfig):
        """SQLModel configuration."""
        pass