"""CRUD operations for Article model."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlmodel import Session, select

from local_newsifier.models.article import Article
# Legacy import for compatibility during transition
from local_newsifier.models.database import ArticleDB


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
    
    # Use proper table class
    from local_newsifier.models.article import Article as ArticleModel
    db_article = ArticleModel(**article_data)
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
    # Use session.get with the proper table class
    from local_newsifier.models.article import Article as ArticleModel
    return session.get(ArticleModel, article_id)


def get_article_by_url(session: Session, url: str) -> Optional[Article]:
    """Get an article by URL.
    
    Args:
        session: Database session
        url: URL of the article to get
        
    Returns:
        Article if found, None otherwise
    """
    # We can't select a class, only a specific table column object
    # Import the actual class instance with table=True
    from local_newsifier.models.article import Article as ArticleModel
    statement = select(ArticleModel).where(ArticleModel.url == url)
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
    # Use proper table class
    from local_newsifier.models.article import Article as ArticleModel
    article = session.get(ArticleModel, article_id)
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
    # We can't select a class, only a specific table column object
    # Import the actual class instance with table=True
    from local_newsifier.models.article import Article as ArticleModel
    statement = select(ArticleModel).where(ArticleModel.status == status)
    return session.exec(statement).all()