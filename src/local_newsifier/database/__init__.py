"""Database package for the Local Newsifier application.

This package provides database access functions, classes, and utilities.
It includes a compatibility layer for existing code that uses DatabaseManager
as well as new adapter functions for direct access to CRUD operations.
"""

from local_newsifier.database.engine import (
    create_db_and_tables,
    create_session_factory,
    get_engine,
    get_session,
    transaction,
)
from local_newsifier.database.manager import DatabaseManager
from local_newsifier.database.adapter import (
    SessionManager,
    add_analysis_result,
    add_entity,
    add_entity_mention_context,
    add_entity_profile,
    add_entity_relationship,
    create_article,
    create_canonical_entity,
    get_all_canonical_entities,
    get_analysis_results_by_article,
    get_article,
    get_article_by_url,
    get_articles_by_status,
    get_articles_mentioning_entity,
    get_canonical_entities_by_type,
    get_canonical_entity,
    get_canonical_entity_by_name,
    get_entities_by_article,
    get_entity_mentions_count,
    get_entity_profile,
    get_entity_sentiment_trend,
    get_entity_timeline,
    update_article_status,
    update_entity_profile,
    with_session,
)

__all__ = [
    # Engine functions
    "create_db_and_tables",
    "create_session_factory",
    "get_engine",
    "get_session",
    "transaction",
    
    # Legacy DatabaseManager
    "DatabaseManager",
    
    # Adapter functions and classes
    "SessionManager",
    "with_session",
    "add_analysis_result",
    "add_entity",
    "add_entity_mention_context",
    "add_entity_profile",
    "add_entity_relationship",
    "create_article",
    "create_canonical_entity",
    "get_all_canonical_entities",
    "get_analysis_results_by_article",
    "get_article",
    "get_article_by_url",
    "get_articles_by_status",
    "get_articles_mentioning_entity",
    "get_canonical_entities_by_type",
    "get_canonical_entity",
    "get_canonical_entity_by_name",
    "get_entities_by_article",
    "get_entity_mentions_count",
    "get_entity_profile",
    "get_entity_sentiment_trend",
    "get_entity_timeline",
    "update_article_status",
    "update_entity_profile",
]