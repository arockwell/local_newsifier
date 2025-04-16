"""Base database model with common fields for all models using SQLModel."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel as _SQLModel
from sqlalchemy import Column, DateTime


class SQLModel(_SQLModel):
    """Base SQLModel with timezone-aware timestamps."""
    
    class Config:
        """SQLModel configuration."""
        arbitrary_types_allowed = True


class TimestampModel(SQLModel):
    """Base model with timestamp fields."""

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            nullable=False
        )
    )
    
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            default=lambda: datetime.now(timezone.utc),
            onupdate=lambda: datetime.now(timezone.utc),
            nullable=False
        )
    )


class Base(TimestampModel):
    """Base model for all database models."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Keep backwards compatibility with SQLAlchemy models
    __table_args__ = {'extend_existing': True}
    
    class Config:
        """SQLModel configuration."""
        orm_mode = True