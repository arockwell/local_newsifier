"""Base models for the application using SQLModel."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import MetaData
from sqlmodel import Field, SQLModel

# Create a separate metadata for SQLModel models
# This avoids conflicts with existing SQLAlchemy models
sqlmodel_metadata = MetaData(schema="sqlmodel")

# Custom SQLModel base class with separate metadata
class SQLModelBase(SQLModel):
    """Custom base SQLModel with separate metadata to avoid conflicts."""
    
    class Config:
        """Custom config with separate metadata."""
        
        orm_mode = True
        # Prevent SQLModel from registering our schema twice
        table = False


class TimestampMixin(SQLModel):
    """Mixin that adds timestamp fields to models."""
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )