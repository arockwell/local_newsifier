"""Base database model with common fields for all models."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Integer, MetaData
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base


class BaseModel:
    """Base SQLAlchemy model with common fields."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        """Create tablename from class name."""
        return cls.__name__.lower()
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


# Create a shared metadata instance
metadata = MetaData()

# Create a base class for all models
Base = declarative_base(cls=BaseModel, metadata=metadata)