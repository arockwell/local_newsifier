"""Base database model definitions using SQLModel."""

from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class TableBase(SQLModel):
    """Base model with common fields for all database tables.

    This is not a table itself but provides common fields for all tables.
    """

    # These fields will be included in all models that inherit from TableBase
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC).replace(tzinfo=None),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC).replace(tzinfo=None)},
    )
