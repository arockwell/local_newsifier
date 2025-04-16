"""Base database model definitions using SQLModel only."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable, TypeVar, Generic, Generator, Type

from sqlmodel import Field, SQLModel, Session, create_engine

# Type variables
T = TypeVar('T')

# Base class for table models with timestamps
class TableBase(SQLModel, table=True):
    """Base model for all database tables with a primary key and timestamps."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": datetime.now(timezone.utc)}
    )
    
    class Config:
        """SQLModel configuration."""
        arbitrary_types_allowed = True
        from_attributes = True


# For non-table schema classes
class SchemaBase(SQLModel):
    """Base model for non-table schema classes."""
    
    class Config:
        """SQLModel configuration."""
        arbitrary_types_allowed = True
        from_attributes = True


# Provide compatibility for code that still uses Base
# This will work during migration but should be phased out
Base = TableBase