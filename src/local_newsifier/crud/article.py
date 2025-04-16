"""CRUD operations for articles."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.pydantic_models import Article, ArticleCreate


class CRUDArticle(CRUDBase[ArticleDB, ArticleCreate, Article]):
    """CRUD operations for articles."""

    def get_by_url(self, db: Session, *, url: str) -> Optional[Article]:
        """Get an article by URL.

        Args:
            db: Database session
            url: URL of the article to get

        Returns:
            Article if found, None otherwise
        """
        db_article = db.query(ArticleDB).filter(ArticleDB.url == url).first()
        return Article.model_validate(db_article) if db_article else None

    def create(self, db: Session, *, obj_in: ArticleCreate) -> Article:
        """Create a new article.

        Args:
            db: Database session
            obj_in: Article data to create

        Returns:
            Created article
        """
        article_data = obj_in.model_dump()
        if "scraped_at" not in article_data or article_data["scraped_at"] is None:
            article_data["scraped_at"] = datetime.now(timezone.utc)
        
        db_article = ArticleDB(**article_data)
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return Article.model_validate(db_article)

    def update_status(self, db: Session, *, article_id: int, status: str) -> Optional[Article]:
        """Update an article's status.

        Args:
            db: Database session
            article_id: ID of the article to update
            status: New status

        Returns:
            Updated article if found, None otherwise
        """
        db_article = db.query(ArticleDB).filter(ArticleDB.id == article_id).first()
        if db_article:
            db_article.status = status
            db.commit()
            db.refresh(db_article)
            return Article.model_validate(db_article)
        return None

    def get_by_status(self, db: Session, *, status: str) -> List[Article]:
        """Get all articles with a specific status.

        Args:
            db: Database session
            status: Status to filter by

        Returns:
            List of articles with the specified status
        """
        db_articles = db.query(ArticleDB).filter(ArticleDB.status == status).all()
        return [Article.model_validate(article) for article in db_articles]


article = CRUDArticle(ArticleDB, Article)