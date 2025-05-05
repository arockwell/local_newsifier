"""Example API router for article management using simplified error-handled CRUD."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.crud.simple_error_handling import handle_crud_errors
from local_newsifier.di.crud_providers import get_article_crud
from local_newsifier.models.article import Article


router = APIRouter(prefix="/simple-articles", tags=["simple-articles"])


class ArticleCreate(BaseModel):
    title: str
    content: str
    url: HttpUrl
    source: str
    published_at: Optional[datetime] = None
    status: str = "new"


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None


class ArticleResponse(BaseModel):
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
async def create_article(
    article: ArticleCreate, 
    db: Session = Depends(get_session),
    article_crud = Depends(get_article_crud)
):
    article_dict = article.model_dump()
    if not article_dict.get("published_at"):
        article_dict["published_at"] = datetime.now()
    
    article_dict["scraped_at"] = datetime.now()
    
    return article_crud.create(db, obj_in=article_dict)


@router.get("/{article_id}", response_model=ArticleResponse)
@handle_crud_errors
async def get_article(
    article_id: int = Path(..., title="Article ID"),
    db: Session = Depends(get_session),
    article_crud = Depends(get_article_crud)
):
    return article_crud.get(db, article_id)


@router.put("/{article_id}", response_model=ArticleResponse)
@handle_crud_errors
async def update_article(
    article_update: ArticleUpdate,
    article_id: int = Path(...),
    db: Session = Depends(get_session),
    article_crud = Depends(get_article_crud)
):
    article = article_crud.get(db, article_id)
    return article_crud.update(
        db, db_obj=article, obj_in=article_update.model_dump(exclude_unset=True)
    )


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_crud_errors
async def delete_article(
    article_id: int = Path(...),
    db: Session = Depends(get_session),
    article_crud = Depends(get_article_crud)
):
    article_crud.remove(db, id=article_id)
    return None


@router.get("/", response_model=List[ArticleResponse])
@handle_crud_errors
async def list_articles(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    days: Optional[int] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
    db: Session = Depends(get_session),
    article_crud = Depends(get_article_crud)
):
    return article_crud.get_multi(db, skip=skip, limit=limit)