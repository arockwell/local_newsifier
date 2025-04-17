"""Base database model definitions using SQLModel."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class TableBase(SQLModel):
    """Base model with common fields for all database tables.
    
    This is not a table itself but provides common fields for all tables.
    """
    
    # These fields will be included in all models that inherit from TableBase
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )