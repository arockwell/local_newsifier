"""CRUD operations for articles with error handling."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union

from fastapi_injectable import injectable
from sqlmodel import Session, select

from local_newsifier.crud.error_handled_base import ErrorHandledCRUD, handle_crud_error
from local_newsifier.models.article import Article


class CRUDArticle(ErrorHandledCRUD[Article]):
    """CRUD operations for articles with error handling."""

    @handle_crud_error
    def get_by_url(self, db: Session, *, url: str) -> Article:
        """Get an article by URL."""
        statement = select(Article).where(Article.url == url)
        result = db.exec(statement).first()
        
        if result is None:
            from local_newsifier.crud.error_handled_base import EntityNotFoundError
            raise EntityNotFoundError(
                f"Article with URL '{url}' not found",
                context={"url": url, "model": self.model.__name__},
            )
            
        return result

    @handle_crud_error
    def create(
        self, db: Session, *, obj_in: Union[Dict[str, Any], Article]
    ) -> Article:
        """Create a new article with error handling."""
        # Handle dict or model instance
        if isinstance(obj_in, dict):
            article_data = obj_in
        else:
            article_data = obj_in.model_dump(exclude_unset=True)
            
        # Add scraped_at if not provided
        if "scraped_at" not in article_data or article_data["scraped_at"] is None:
            article_data["scraped_at"] = datetime.now(timezone.utc)

        # Call the parent implementation (with error handling)
        if isinstance(obj_in, dict):
            return super().create(db, obj_in=article_data)
        else:
            # Update the object with scraped_at if needed
            if not hasattr(obj_in, "scraped_at") or obj_in.scraped_at is None:
                obj_in.scraped_at = article_data["scraped_at"]
            return super().create(db, obj_in=obj_in)

    @handle_crud_error
    def update_status(
        self, db: Session, *, article_id: int, status: str
    ) -> Article:
        """Update an article's status with error handling."""
        db_article = db.exec(select(Article).where(Article.id == article_id)).first()
        
        if db_article is None:
            from local_newsifier.crud.error_handled_base import EntityNotFoundError
            raise EntityNotFoundError(
                f"Article with ID {article_id} not found",
                context={"article_id": article_id, "model": self.model.__name__},
            )

        db_article.status = status
        db.add(db_article)
        db.commit()
        db.refresh(db_article)
        return db_article

    @handle_crud_error
    def get_by_status(self, db: Session, *, status: str) -> List[Article]:
        """Get all articles with a specific status with error handling."""
        return db.exec(select(Article).where(Article.status == status)).all()
        
    @handle_crud_error
    def get_by_date_range(
        self, 
        db: Session, 
        *, 
        start_date: datetime, 
        end_date: datetime,
        source: Optional[str] = None
    ) -> List[Article]:
        """Get articles within a date range with error handling."""
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


# Create a singleton instance for backward compatibility
article = CRUDArticle(Article)


# Factory function for DI
@injectable(use_cache=True)
def get_article_crud():
    """Get a CRUDArticle instance for dependency injection."""
    return article