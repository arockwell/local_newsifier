"""CRUD operations package."""

from local_newsifier.crud.article import (
    create_article,
    get_article,
    get_article_by_url,
    update_article_status,
    get_articles_by_status,
)

__all__ = [
    "create_article",
    "get_article",
    "get_article_by_url",
    "update_article_status",
    "get_articles_by_status",
]