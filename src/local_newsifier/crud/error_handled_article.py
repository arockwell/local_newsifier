"""Error-handled CRUD operations for articles."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlmodel import Session, select

from local_newsifier.crud.error_handled_base import (EntityNotFoundError,
                                                     ErrorHandledCRUD,
                                                     handle_crud_error)
from local_newsifier.models.article import Article


class ErrorHandledCRUDArticle(ErrorHandledCRUD[Article]):
    """CRUD operations for articles with standardized error handling."""

    @handle_crud_error
    def get_by_url(self, db: Session, *, url: str) -> Article:
        """Get an article by URL with error handling.

        Args:
            db: Database session
            url: URL of the article to get

        Returns:
            Article if found

        Raises:
            EntityNotFoundError: If the article with the given URL does not exist
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        statement = select(Article).where(Article.url == url)
        result = db.exec(statement).first()

        if result is None:
            raise EntityNotFoundError(
                f"Article with URL '{url}' not found",
                context={"url": url, "model": self.model.__name__},
            )

        return result

    @handle_crud_error
    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], Article]) -> Article:
        """Create a new article with error handling.

        Args:
            db: Database session
            obj_in: Article data to create

        Returns:
            Created article

        Raises:
            DuplicateEntityError: If an article with the same URL already exists
            ValidationError: If the article data fails validation
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
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
    def update_status(self, db: Session, *, article_id: int, status: str) -> Article:
        """Update an article's status with error handling.

        Args:
            db: Database session
            article_id: ID of the article to update
            status: New status

        Returns:
            Updated article

        Raises:
            EntityNotFoundError: If the article with the given ID does not exist
            ValidationError: If the status is invalid
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
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
        """Get all articles with a specific status with error handling.

        Args:
            db: Database session
            status: Status to filter by

        Returns:
            List of articles with the specified status

        Raises:
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        return db.exec(select(Article).where(Article.status == status)).all()

    @handle_crud_error
    def get_by_date_range(
        self,
        db: Session,
        *,
        start_date: datetime,
        end_date: datetime,
        source: Optional[str] = None,
    ) -> List[Article]:
        """Get articles within a date range with error handling.

        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            source: Optional source to filter by

        Returns:
            List of articles within the date range

        Raises:
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        query = select(Article).where(
            Article.published_at >= start_date, Article.published_at <= end_date
        )

        # Add source filter if provided
        if source:
            query = query.where(Article.source == source)

        # Order by published date
        query = query.order_by(Article.published_at)

        return db.exec(query).all()


# Create an instance of the error handled article CRUD
error_handled_article = ErrorHandledCRUDArticle(Article)
