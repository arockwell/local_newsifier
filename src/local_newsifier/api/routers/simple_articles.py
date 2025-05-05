"""Example API router for article management using simplified error-handled CRUD.

This module demonstrates how to use the simplified ErrorHandledCRUD with FastAPI endpoints.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from fastapi_injectable import Inject, injectable
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.crud.simple_error_handling import handle_crud_errors
from local_newsifier.models.article import Article
from local_newsifier.di.crud_providers import get_error_handled_crud_factory


router = APIRouter(prefix="/simple-articles", tags=["simple-articles"])


class ArticleCreate(BaseModel):
    """Request model for creating an article."""
    
    title: str
    content: str
    url: HttpUrl
    source: str
    published_at: Optional[datetime] = None
    status: str = "new"


class ArticleUpdate(BaseModel):
    """Request model for updating an article."""
    
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None


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


@injectable
def get_article_crud(crud_factory=Inject(get_error_handled_crud_factory)):
    """Get an error-handled CRUD object for articles."""
    return crud_factory(Article)


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
@handle_crud_errors
async def create_article(
    article: ArticleCreate, 
    db: Session = Depends(get_session),
    article_crud: get_article_crud = Inject(get_article_crud)
):
    """Create a new article.
    
    This endpoint demonstrates how the simplified ErrorHandledCRUD automatically 
    handles database errors and converts them to appropriate HTTP responses.
    
    Args:
        article: Article data to create
        db: Database session
        article_crud: CRUD object for article operations
        
    Returns:
        Created article data
        
    Raises:
        HTTPException: With appropriate status code for various error conditions
    """
    # Add current time as published_at if not provided
    article_dict = article.model_dump()
    if not article_dict.get("published_at"):
        article_dict["published_at"] = datetime.now()
    
    # Add current time as scraped_at
    article_dict["scraped_at"] = datetime.now()
    
    # Create the article with error handling
    created_article = article_crud.create(db, obj_in=article_dict)
    return created_article


@router.get("/{article_id}", response_model=ArticleResponse)
@handle_crud_errors
async def get_article(
    article_id: int = Path(..., title="Article ID", description="ID of the article to retrieve"),
    db: Session = Depends(get_session),
    article_crud: get_article_crud = Inject(get_article_crud)
):
    """Get an article by ID.
    
    Args:
        article_id: ID of the article to retrieve
        db: Database session
        article_crud: CRUD object for article operations
        
    Returns:
        Article data
        
    Raises:
        HTTPException: 404 if article not found, with standardized error format
    """
    return article_crud.get(db, article_id)


@router.put("/{article_id}", response_model=ArticleResponse)
@handle_crud_errors
async def update_article(
    article_update: ArticleUpdate,
    article_id: int = Path(..., title="Article ID", description="ID of the article to update"),
    db: Session = Depends(get_session),
    article_crud: get_article_crud = Inject(get_article_crud)
):
    """Update an article.
    
    Args:
        article_update: Article data to update
        article_id: ID of the article to update
        db: Database session
        article_crud: CRUD object for article operations
        
    Returns:
        Updated article data
        
    Raises:
        HTTPException: With appropriate status code for various error conditions
    """
    # Get the article first
    article = article_crud.get(db, article_id)
    
    # Update the article
    updated_article = article_crud.update(
        db, db_obj=article, obj_in=article_update.model_dump(exclude_unset=True)
    )
    
    return updated_article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_crud_errors
async def delete_article(
    article_id: int = Path(..., title="Article ID", description="ID of the article to delete"),
    db: Session = Depends(get_session),
    article_crud: get_article_crud = Inject(get_article_crud)
):
    """Delete an article.
    
    Args:
        article_id: ID of the article to delete
        db: Database session
        article_crud: CRUD object for article operations
        
    Returns:
        No content
        
    Raises:
        HTTPException: 404 if article not found, with standardized error format
    """
    article_crud.remove(db, id=article_id)
    return None


@router.get("/", response_model=List[ArticleResponse])
@handle_crud_errors
async def list_articles(
    status: Optional[str] = Query(None, title="Article Status", description="Filter by article status"),
    source: Optional[str] = Query(None, title="Article Source", description="Filter by article source"),
    days: Optional[int] = Query(None, title="Days", description="Number of days to look back"),
    skip: int = Query(0, title="Skip", description="Number of articles to skip"),
    limit: int = Query(100, title="Limit", description="Maximum number of articles to return"),
    db: Session = Depends(get_session),
    article_crud: get_article_crud = Inject(get_article_crud)
):
    """List articles with pagination.
    
    This is a simplified version that only supports basic pagination.
    For more advanced filtering, you'd need to extend the ErrorHandledCRUD
    with additional methods like in the original implementation.
    
    Args:
        status: Optional filter by article status (not implemented in this example)
        source: Optional filter by article source (not implemented in this example)
        days: Optional number of days to look back (not implemented in this example)
        skip: Number of articles to skip
        limit: Maximum number of articles to return
        db: Database session
        article_crud: CRUD object for article operations
        
    Returns:
        List of article data
    """
    # In a real implementation, you would add methods to ErrorHandledCRUD for filtering
    # based on status, source, date range, etc. For this example, we just use the basic
    # get_multi method.
    return article_crud.get_multi(db, skip=skip, limit=limit)