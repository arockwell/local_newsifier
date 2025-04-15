"""CRUD operations for Article model."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlmodel import Session, select

from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.analysis_result import AnalysisResult


def create_article(session: Session, article_data: Dict[str, Any]) -> Article:
    """Create a new article in the database.
    
    Args:
        session: Database session
        article_data: Article data dictionary
        
    Returns:
        Created article
    """
    if 'scraped_at' not in article_data or article_data['scraped_at'] is None:
        article_data['scraped_at'] = datetime.now(timezone.utc)
    
    db_article = Article(**article_data)
    session.add(db_article)
    session.commit()
    session.refresh(db_article)
    return db_article


def get_article(session: Session, article_id: int) -> Optional[Article]:
    """Get an article by ID.
    
    Args:
        session: Database session
        article_id: ID of the article to get
        
    Returns:
        Article if found, None otherwise
    """
    return session.get(Article, article_id)


def get_article_by_url(session: Session, url: str) -> Optional[Article]:
    """Get an article by URL.
    
    Args:
        session: Database session
        url: URL of the article to get
        
    Returns:
        Article if found, None otherwise
    """
    statement = select(Article).where(Article.url == url)
    return session.exec(statement).first()


def update_article_status(session: Session, article_id: int, status: str) -> Optional[Article]:
    """Update an article's status.
    
    Args:
        session: Database session
        article_id: ID of the article to update
        status: New status
        
    Returns:
        Updated article if found, None otherwise
    """
    article = session.get(Article, article_id)
    if article:
        article.status = status
        article.updated_at = datetime.now(timezone.utc)
        session.add(article)
        session.commit()
        session.refresh(article)
    return article


def get_articles_by_status(session: Session, status: str) -> List[Article]:
    """Get all articles with a specific status.
    
    Args:
        session: Database session
        status: Status to filter by
        
    Returns:
        List of articles with the specified status
    """
    statement = select(Article).where(Article.status == status)
    return session.exec(statement).all()


def get_articles_in_timeframe(
    session: Session,
    start_date: datetime,
    end_date: Optional[datetime] = None,
    source: Optional[str] = None,
) -> List[Article]:
    """Get articles within a specific timeframe.
    
    Args:
        session: Database session
        start_date: Start date for the timeframe
        end_date: End date for the timeframe
        source: Optional source to filter by
        
    Returns:
        List of articles within the timeframe
    """
    if end_date is None:
        end_date = datetime.now(timezone.utc)
    
    statement = select(Article).where(
        Article.published_at >= start_date,
        Article.published_at <= end_date
    )
    
    if source:
        statement = statement.where(Article.source == source)
    
    return session.exec(statement).all()


def get_entities_by_article(session: Session, article_id: int) -> List[Entity]:
    """Get all entities for an article.
    
    Args:
        session: Database session
        article_id: ID of the article
        
    Returns:
        List of entities for the article
    """
    statement = select(Entity).where(Entity.article_id == article_id)
    return session.exec(statement).all()


def get_analysis_results_by_article(session: Session, article_id: int) -> List[AnalysisResult]:
    """Get all analysis results for an article.
    
    Args:
        session: Database session
        article_id: ID of the article
        
    Returns:
        List of analysis results for the article
    """
    statement = select(AnalysisResult).where(AnalysisResult.article_id == article_id)
    return session.exec(statement).all()