"""Database models for the news analysis system."""

import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import (JSON, Column, DateTime, Float, ForeignKey, Integer,
                        String, create_engine)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


# SQLAlchemy Models
class ArticleDB(Base):
    """Database model for news articles."""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    title = Column(String)
    source = Column(String)
    published_at = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    content = Column(String)
    status = Column(String)  # e.g., "scraped", "analyzed", "error"

    # Relationships
    entities = relationship("EntityDB", back_populates="article")
    analysis_results = relationship("AnalysisResultDB", back_populates="article")


class EntityDB(Base):
    """Database model for named entities found in articles."""

    __tablename__ = "entities"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    text = Column(String)
    entity_type = Column(String)  # e.g., "PERSON", "ORG", "GPE"
    confidence = Column(Float)

    # Relationships
    article = relationship("ArticleDB", back_populates="entities")


class AnalysisResultDB(Base):
    """Database model for analysis results."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    analysis_type = Column(String)  # e.g., "NER", "sentiment"
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    article = relationship("ArticleDB", back_populates="analysis_results")


# Pydantic Models
class ArticleBase(BaseModel):
    """Base Pydantic model for articles."""

    url: str
    title: Optional[str] = None
    source: Optional[str] = None
    published_at: Optional[datetime] = None
    content: Optional[str] = None
    status: Optional[str] = None


class ArticleCreate(ArticleBase):
    """Pydantic model for creating articles."""

    pass


class Article(ArticleBase):
    """Pydantic model for articles with relationships."""

    id: int
    scraped_at: datetime
    entities: List["Entity"] = []
    analysis_results: List["AnalysisResult"] = []

    class Config:
        """Pydantic config."""

        from_attributes = True


class EntityBase(BaseModel):
    """Base Pydantic model for entities."""

    text: str
    entity_type: str
    confidence: float


class EntityCreate(EntityBase):
    """Pydantic model for creating entities."""

    article_id: int


class Entity(EntityBase):
    """Pydantic model for entities with relationships."""

    id: int
    article_id: int

    class Config:
        """Pydantic config."""

        from_attributes = True


class AnalysisResultBase(BaseModel):
    """Base Pydantic model for analysis results."""

    analysis_type: str
    results: dict


class AnalysisResultCreate(AnalysisResultBase):
    """Pydantic model for creating analysis results."""

    article_id: int


class AnalysisResult(AnalysisResultBase):
    """Pydantic model for analysis results with relationships."""

    id: int
    article_id: int
    created_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


# Database initialization
def init_db(db_url: str) -> Engine:
    """Initialize the database and create tables.

    Args:
        db_url: Database connection URL

    Returns:
        SQLAlchemy engine instance
    """
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine: Engine) -> sessionmaker:
    """Create a session factory for database operations.

    Args:
        engine: SQLAlchemy engine instance

    Returns:
        SQLAlchemy session factory
    """
    return sessionmaker(bind=engine)
