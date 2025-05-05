"""CRUD operations for articles with error handling."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Union

from fastapi_injectable import injectable
from sqlmodel import Session, select

from local_newsifier.crud.error_handled_base import ErrorHandledCRUD, handle_crud_error, EntityNotFoundError
from local_newsifier.models.article import Article


class CRUDArticle(ErrorHandledCRUD[Article]):
    """CRUD operations for articles with error handling."""

    @handle_crud_error
    def get_by_url(self, db: Session, *, url: str) -> Article:
        result = db.exec(select(Article).where(Article.url == url)).first()
        if result is None:
            raise EntityNotFoundError(
                f"Article with URL '{url}' not found",
                context={"url": url, "model": self.model.__name__},
            )
        return result

    @handle_crud_error
    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], Article]) -> Article:
        # Add scraped_at if not provided
        article_data = obj_in.model_dump(exclude_unset=True) if isinstance(obj_in, Article) else obj_in
        if "scraped_at" not in article_data or article_data["scraped_at"] is None:
            now = datetime.now(timezone.utc)
            article_data["scraped_at"] = now
            if isinstance(obj_in, Article) and (not hasattr(obj_in, "scraped_at") or obj_in.scraped_at is None):
                obj_in.scraped_at = now
        return super().create(db, obj_in=obj_in if isinstance(obj_in, Article) else article_data)

    @handle_crud_error
    def update_status(self, db: Session, *, article_id: int, status: str) -> Article:
        db_article = db.exec(select(Article).where(Article.id == article_id)).first()
        if db_article is None:
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
        return db.exec(select(Article).where(Article.status == status)).all()
        
    @handle_crud_error
    def get_by_date_range(
        self, db: Session, *, start_date: datetime, end_date: datetime,
        source: Optional[str] = None
    ) -> List[Article]:
        query = select(Article).where(
            Article.published_at >= start_date,
            Article.published_at <= end_date
        )
        if source:
            query = query.where(Article.source == source)
        return db.exec(query.order_by(Article.published_at)).all()


# Create a singleton instance for backward compatibility
article = CRUDArticle(Article)


# Factory function for DI
@injectable(use_cache=True)
def get_article_crud():
    return article