"""CRUD operations for articles."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union

from sqlmodel import Session, select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.article import Article


class CRUDArticle(CRUDBase[Article]):
    """CRUD operations for articles."""

    def get_by_url(self, db: Session, *, url: str) -> Optional[Article]:
        """Get an article by URL.

        Args:
            db: Database session
            url: URL of the article to get

        Returns:
            Article if found, None otherwise
        """
        statement = select(Article).where(Article.url == url)
        results = db.exec(statement)
        return results.first()

    def create(
        self, db: Session, *, obj_in: Union[Dict[str, Any], Article]
    ) -> Article:
        """Create a new article.

        Args:
            db: Database session
            obj_in: Article data to create

        Returns:
            Created article
        """
        # Handle dict or model instance
        if isinstance(obj_in, dict):
            article_data = obj_in
        else:
            article_data = obj_in.model_dump(exclude_unset=True)
            
        # Add scraped_at if not provided
        if "scraped_at" not in article_data or article_data["scraped_at"] is None:
            article_data["scraped_at"] = datetime.now(timezone.utc)

        db_article = Article(**article_data)
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return db_article

    def update_status(
        self, db: Session, *, article_id: int, status: str
    ) -> Optional[Article]:
        """Update an article's status.

        Args:
            db: Database session
            article_id: ID of the article to update
            status: New status

        Returns:
            Updated article if found, None otherwise
        """
        db_article = db.exec(select(Article).where(Article.id == article_id)).first()
        
        if db_article:
            db_article.status = status
            db.add(db_article)
            db.commit()
            db.refresh(db_article)
            return db_article
        return None

    def get_by_status(self, db: Session, *, status: str) -> List[Article]:
        """Get all articles with a specific status.

        Args:
            db: Database session
            status: Status to filter by

        Returns:
            List of articles with the specified status
        """
        return db.exec(select(Article).where(Article.status == status)).all()
        
    def get_by_date_range(
        self, 
        db: Session, 
        *, 
        start_date: datetime, 
        end_date: datetime,
        source: Optional[str] = None
    ) -> List[Article]:
        """Get articles within a date range.

        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            source: Optional source to filter by

        Returns:
            List of articles within the date range
        """
        query = select(Article).where(
            Article.published_at >= start_date,
            Article.published_at <= end_date
        )
        
        # Add source filter if provided
        if source:
            query = query.where(Article.source == source)
            
        # Order by published date
        query = query.order_by(Article.published_at)
        
        return db.exec(query).all()


article = CRUDArticle(Article)
