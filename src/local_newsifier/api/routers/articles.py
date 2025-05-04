"""
API router for article management using error-handled CRUD operations.

This module demonstrates how to use the ErrorHandledCRUD base class with API endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import BaseModel, Field, HttpUrl, validator
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.crud.error_handled_article import error_handled_article
from local_newsifier.crud.error_handling import handle_crud_errors

router = APIRouter(prefix="/articles", tags=["articles"])


class ArticleCreate(BaseModel):
    """Request model for creating an article."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    url: HttpUrl
    source: str = Field(..., min_length=1, max_length=100)
    published_at: Optional[datetime] = None
    status: str = "new"

    @validator("status")
    def validate_status(cls, v):
        """Validate that status is one of the allowed values."""
        allowed_statuses = ["new", "processed", "analyzed", "archived"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class ArticleUpdate(BaseModel):
    """Request model for updating an article."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    source: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        """Validate that status is one of the allowed values if provided."""
        if v is None:
            return v

        allowed_statuses = ["new", "processed", "analyzed", "archived"]
        if v not in allowed_statuses:
            raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v


class ArticleResponse(BaseModel):
    """Response model for article data."""

    id: int
    title: str
    content: str
    url: HttpUrl
    source: str
    published_at: datetime
    status: str
    scraped_at: datetime


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
@handle_crud_errors
async def create_article(article: ArticleCreate, db: Session = Depends(get_session)):
    """
    Create a new article.

    This endpoint demonstrates how the ErrorHandledCRUD automatically handles
    database errors and converts them to appropriate HTTP responses.

    Args:
        article: Article data to create
        db: Database session

    Returns:
        Created article data

    Raises:
        HTTPException: With appropriate status code for various error conditions
    """
    # The handle_crud_errors decorator will catch any CRUDError raised
    # by the error_handled_article CRUD operations and convert them to
    # appropriate HTTPExceptions with standardized error responses
    created_article = error_handled_article.create(db, obj_in=article.model_dump())
    return created_article


@router.get("/{article_id}", response_model=ArticleResponse)
@handle_crud_errors
async def get_article(
    article_id: int = Path(
        ..., title="Article ID", description="ID of the article to retrieve"
    ),
    db: Session = Depends(get_session),
):
    """
    Get an article by ID.

    Args:
        article_id: ID of the article to retrieve
        db: Database session

    Returns:
        Article data

    Raises:
        HTTPException: 404 if article not found, with standardized error format
    """
    return error_handled_article.get(db, article_id)


@router.put("/{article_id}", response_model=ArticleResponse)
@handle_crud_errors
async def update_article(
    article_update: ArticleUpdate,
    article_id: int = Path(
        ..., title="Article ID", description="ID of the article to update"
    ),
    db: Session = Depends(get_session),
):
    """
    Update an article.

    Args:
        article_update: Article data to update
        article_id: ID of the article to update
        db: Database session

    Returns:
        Updated article data

    Raises:
        HTTPException: With appropriate status code for various error conditions
    """
    # Get the article first (this will raise EntityNotFoundError if not found)
    article = error_handled_article.get(db, article_id)

    # Update the article
    updated_article = error_handled_article.update(
        db, db_obj=article, obj_in=article_update.model_dump(exclude_unset=True)
    )

    return updated_article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_crud_errors
async def delete_article(
    article_id: int = Path(
        ..., title="Article ID", description="ID of the article to delete"
    ),
    db: Session = Depends(get_session),
):
    """
    Delete an article.

    Args:
        article_id: ID of the article to delete
        db: Database session

    Returns:
        No content

    Raises:
        HTTPException: 404 if article not found, with standardized error format
    """
    error_handled_article.remove(db, id=article_id)
    return None


@router.get("/url/{url:path}", response_model=ArticleResponse)
@handle_crud_errors
async def get_article_by_url(
    url: str = Path(
        ..., title="Article URL", description="URL of the article to retrieve"
    ),
    db: Session = Depends(get_session),
):
    """
    Get an article by URL.

    Args:
        url: URL of the article to retrieve
        db: Database session

    Returns:
        Article data

    Raises:
        HTTPException: 404 if article not found, with standardized error format
    """
    # Validate the URL string is a valid URL
    try:
        validated_url = HttpUrl(url)
        return error_handled_article.get_by_url(db, url=str(validated_url))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid URL format: {url}"
        )


@router.get("/", response_model=List[ArticleResponse])
@handle_crud_errors
async def list_articles(
    status: Optional[str] = Query(
        None, title="Article Status", description="Filter by article status"
    ),
    source: Optional[str] = Query(
        None, title="Article Source", description="Filter by article source"
    ),
    days: Optional[int] = Query(
        None, title="Days", description="Number of days to look back"
    ),
    skip: int = Query(0, title="Skip", description="Number of articles to skip"),
    limit: int = Query(
        100, title="Limit", description="Maximum number of articles to return"
    ),
    db: Session = Depends(get_session),
):
    """
    List articles with optional filtering.

    Args:
        status: Optional filter by article status
        source: Optional filter by article source
        days: Optional number of days to look back
        skip: Number of articles to skip
        limit: Maximum number of articles to return
        db: Database session

    Returns:
        List of article data
    """
    if status:
        return error_handled_article.get_by_status(db, status=status)

    if days:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return error_handled_article.get_by_date_range(
            db, start_date=start_date, end_date=end_date, source=source
        )

    # Default to using find_by_attributes for flexible filtering
    attributes = {}
    if source:
        attributes["source"] = source

    if attributes:
        return error_handled_article.find_by_attributes(db, attributes=attributes)

    # No filters, get all with pagination
    return error_handled_article.get_multi(db, skip=skip, limit=limit)
