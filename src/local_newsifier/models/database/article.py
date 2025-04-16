"""Article models for the news analysis system."""

from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, DateTime, String, Text

from local_newsifier.models.database.base import Base


class Article(Base, table=True):
    """SQLModel for articles, combining Pydantic validation and SQLAlchemy ORM."""

    __tablename__ = "articles"
    
    title: str = Field(sa_column=Column(String(255), nullable=False))
    content: str = Field(sa_column=Column(Text, nullable=False))
    url: str = Field(sa_column=Column(String(512), nullable=False, unique=True))
    source: str = Field(sa_column=Column(String(255), nullable=False))
    published_at: datetime
    status: str = Field(sa_column=Column(String(50), nullable=False))
    scraped_at: datetime
    
    # Define relationships - forward references that will be resolved later
    entities: List["Entity"] = Relationship(back_populates="article")
    analysis_results: List["AnalysisResult"] = Relationship(back_populates="article")


# No backward compatibility - we'll refactor references directly