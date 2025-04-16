"""CRUD operations for articles."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlmodel import select, SQLModel

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.database.article import Article


# Create a simple class for article creation
class ArticleCreate(SQLModel):
    """Schema for creating articles."""
    
    url: str
    title: str
    content: str
    source: str
    published_at: datetime
    status: str
    scraped_at: Optional[datetime] = None


class CRUDArticle(CRUDBase[Article, ArticleCreate, Article]):
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

    def create(self, db: Session, *, obj_in: ArticleCreate) -> Article:
        """Create a new article.

        Args:
            db: Database session
            obj_in: Article data to create

        Returns:
            Created article
        """
        article_data = obj_in.model_dump()
        if (
            "scraped_at" not in article_data
            or article_data["scraped_at"] is None
        ):
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
        statement = select(Article).where(Article.id == article_id)
        results = db.exec(statement)
        db_article = results.first()
        
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
        statement = select(Article).where(Article.status == status)
        results = db.exec(statement)
        return results.all()


article = CRUDArticle(Article, ArticleCreate)
