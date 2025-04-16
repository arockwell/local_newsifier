"""Database adapter for migrating from DatabaseManager to CRUD modules.

This module provides adapter functions and classes to make it easier to
migrate from using the DatabaseManager to using CRUD modules directly.
"""

from typing import List, Optional, Any, Dict, Type
from datetime import datetime

from sqlalchemy.orm import Session

from local_newsifier.models.pydantic_models import (
    Article, ArticleCreate, Entity, EntityCreate, AnalysisResult, AnalysisResultCreate
)
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, CanonicalEntityCreate,
    EntityMentionContext, EntityMentionContextCreate,
    EntityProfile, EntityProfileCreate,
    EntityRelationship, EntityRelationshipCreate,
)
from local_newsifier.database.engine import get_session, transaction


class SessionManager:
    """Session manager for database operations.
    
    This class provides a context manager for database sessions, making it
    easier to migrate from DatabaseManager to CRUD modules.
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self.session = None
    
    def __enter__(self):
        """Enter the context manager.
        
        Returns:
            Session: Database session
        """
        self.session_generator = get_session()
        self.session = next(self.session_generator)
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager.
        
        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        try:
            next(self.session_generator, None)
        except StopIteration:
            pass


def with_session(func):
    """Decorator for functions that need a database session.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, session=None, **kwargs):
        """Wrapper function.
        
        Args:
            session: SQLAlchemy session
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of the decorated function
        """
        if session is not None:
            return func(*args, session=session, **kwargs)
        
        with SessionManager() as new_session:
            return func(*args, session=new_session, **kwargs)
    
    return wrapper


@with_session
def create_article(article_data: ArticleCreate, *, session: Session) -> Article:
    """Create a new article.
    
    Args:
        article_data: Article data to create
        session: Database session
        
    Returns:
        Created article
    """
    from local_newsifier.crud.article import article as article_crud
    return article_crud.create(session, obj_in=article_data)


@with_session
def get_article(article_id: int, *, session: Session) -> Optional[Article]:
    """Get an article by ID.
    
    Args:
        article_id: ID of the article to get
        session: Database session
        
    Returns:
        Article if found, None otherwise
    """
    from local_newsifier.crud.article import article as article_crud
    return article_crud.get(session, id=article_id)


@with_session
def get_article_by_url(url: str, *, session: Session) -> Optional[Article]:
    """Get an article by URL.
    
    Args:
        url: URL of the article to get
        session: Database session
        
    Returns:
        Article if found, None otherwise
    """
    from local_newsifier.crud.article import article as article_crud
    return article_crud.get_by_url(session, url=url)


@with_session
def update_article_status(
    article_id: int, status: str, *, session: Session
) -> Optional[Article]:
    """Update an article's status.
    
    Args:
        article_id: ID of the article to update
        status: New status
        session: Database session
        
    Returns:
        Updated article if found, None otherwise
    """
    from local_newsifier.crud.article import article as article_crud
    return article_crud.update_status(session, article_id=article_id, status=status)


@with_session
def get_articles_by_status(status: str, *, session: Session) -> List[Article]:
    """Get all articles with a specific status.
    
    Args:
        status: Status to filter by
        session: Database session
        
    Returns:
        List of articles with the specified status
    """
    from local_newsifier.crud.article import article as article_crud
    return article_crud.get_by_status(session, status=status)


@with_session
def add_entity(entity_data: EntityCreate, *, session: Session) -> Entity:
    """Add an entity to an article.
    
    Args:
        entity_data: Entity data to add
        session: Database session
        
    Returns:
        Created entity
    """
    from local_newsifier.crud.entity import entity as entity_crud
    return entity_crud.create(session, obj_in=entity_data)


@with_session
def get_entities_by_article(article_id: int, *, session: Session) -> List[Entity]:
    """Get all entities for an article.
    
    Args:
        article_id: ID of the article
        session: Database session
        
    Returns:
        List of entities for the article
    """
    from local_newsifier.crud.entity import entity as entity_crud
    return entity_crud.get_by_article(session, article_id=article_id)


@with_session
def add_analysis_result(
    result_data: AnalysisResultCreate, *, session: Session
) -> AnalysisResult:
    """Add an analysis result to an article.
    
    Args:
        result_data: Analysis result data to add
        session: Database session
        
    Returns:
        Created analysis result
    """
    from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
    return analysis_result_crud.create(session, obj_in=result_data)


@with_session
def get_analysis_results_by_article(
    article_id: int, *, session: Session
) -> List[AnalysisResult]:
    """Get all analysis results for an article.
    
    Args:
        article_id: ID of the article
        session: Database session
        
    Returns:
        List of analysis results for the article
    """
    from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
    return analysis_result_crud.get_by_article(session, article_id=article_id)


@with_session
def create_canonical_entity(
    entity_data: CanonicalEntityCreate, *, session: Session
) -> CanonicalEntity:
    """Create a new canonical entity.
    
    Args:
        entity_data: Canonical entity data to create
        session: Database session
        
    Returns:
        Created canonical entity
    """
    from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
    return canonical_entity_crud.create(session, obj_in=entity_data)


@with_session
def get_canonical_entity(
    entity_id: int, *, session: Session
) -> Optional[CanonicalEntity]:
    """Get a canonical entity by ID.
    
    Args:
        entity_id: ID of the canonical entity to get
        session: Database session
        
    Returns:
        Canonical entity if found, None otherwise
    """
    from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
    return canonical_entity_crud.get(session, id=entity_id)


@with_session
def get_canonical_entity_by_name(
    name: str, entity_type: str, *, session: Session
) -> Optional[CanonicalEntity]:
    """Get a canonical entity by name and type.
    
    Args:
        name: Name of the canonical entity
        entity_type: Type of the entity (e.g., "PERSON")
        session: Database session
        
    Returns:
        Canonical entity if found, None otherwise
    """
    from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
    return canonical_entity_crud.get_by_name(
        session, name=name, entity_type=entity_type
    )


@with_session
def get_canonical_entities_by_type(
    entity_type: str, *, session: Session
) -> List[CanonicalEntity]:
    """Get all canonical entities of a specific type.
    
    Args:
        entity_type: Type of entities to get
        session: Database session
        
    Returns:
        List of canonical entities
    """
    from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
    return canonical_entity_crud.get_by_type(session, entity_type=entity_type)


@with_session
def get_all_canonical_entities(
    entity_type: Optional[str] = None, *, session: Session
) -> List[CanonicalEntity]:
    """Get all canonical entities, optionally filtered by type.
    
    Args:
        entity_type: Optional type to filter by
        session: Database session
        
    Returns:
        List of canonical entities
    """
    from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
    return canonical_entity_crud.get_all(session, entity_type=entity_type)


@with_session
def add_entity_mention_context(
    context_data: EntityMentionContextCreate, *, session: Session
) -> EntityMentionContext:
    """Add context for an entity mention.
    
    Args:
        context_data: Entity mention context data to add
        session: Database session
        
    Returns:
        Created entity mention context
    """
    from local_newsifier.crud.entity_mention_context import entity_mention_context as entity_mention_context_crud
    return entity_mention_context_crud.create(session, obj_in=context_data)


@with_session
def add_entity_profile(
    profile_data: EntityProfileCreate, *, session: Session
) -> EntityProfile:
    """Add a new entity profile.
    
    Args:
        profile_data: Entity profile data to add
        session: Database session
        
    Returns:
        Created entity profile
    """
    from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
    try:
        return entity_profile_crud.create(session, obj_in=profile_data)
    except ValueError as e:
        if "Profile already exists" in str(e):
            entity_id = profile_data.canonical_entity_id
            raise ValueError(f"Profile already exists for entity {entity_id}")
        raise


@with_session
def update_entity_profile(
    profile_data: EntityProfileCreate, *, session: Session
) -> EntityProfile:
    """Update an entity profile.
    
    Args:
        profile_data: Profile data to update
        session: Database session
        
    Returns:
        Updated profile
    """
    from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
    return entity_profile_crud.update_or_create(session, obj_in=profile_data)


@with_session
def get_entity_profile(
    entity_id: int, *, session: Session
) -> Optional[EntityProfile]:
    """Get the profile for an entity.
    
    Args:
        entity_id: ID of the entity
        session: Database session
        
    Returns:
        Entity profile if found, None otherwise
    """
    from local_newsifier.crud.entity_profile import entity_profile as entity_profile_crud
    return entity_profile_crud.get_by_entity(session, entity_id=entity_id)


@with_session
def add_entity_relationship(
    relationship_data: EntityRelationshipCreate, *, session: Session
) -> EntityRelationship:
    """Add a relationship between entities.
    
    Args:
        relationship_data: Entity relationship data to add
        session: Database session
        
    Returns:
        Created entity relationship
    """
    from local_newsifier.crud.entity_relationship import entity_relationship as entity_relationship_crud
    return entity_relationship_crud.create_or_update(session, obj_in=relationship_data)


@with_session
def get_entity_mentions_count(entity_id: int, *, session: Session) -> int:
    """Get the count of mentions for an entity.
    
    Args:
        entity_id: ID of the entity
        session: Database session
        
    Returns:
        Count of mentions
    """
    from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
    return canonical_entity_crud.get_mentions_count(session, entity_id=entity_id)


@with_session
def get_entity_timeline(
    entity_id: int, start_date: datetime, end_date: datetime, *, session: Session
) -> List[Dict[str, Any]]:
    """Get the timeline of entity mentions.
    
    Args:
        entity_id: ID of the entity
        start_date: Start date for the timeline
        end_date: End date for the timeline
        session: Database session
        
    Returns:
        List of timeline entries
    """
    from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
    return canonical_entity_crud.get_entity_timeline(
        session, entity_id=entity_id, start_date=start_date, end_date=end_date
    )


@with_session
def get_entity_sentiment_trend(
    entity_id: int, start_date: datetime, end_date: datetime, *, session: Session
) -> List[Dict[str, Any]]:
    """Get the sentiment trend for an entity.
    
    Args:
        entity_id: ID of the entity
        start_date: Start date for the trend
        end_date: End date for the trend
        session: Database session
        
    Returns:
        List of sentiment trend entries
    """
    from local_newsifier.crud.entity_mention_context import entity_mention_context as entity_mention_context_crud
    return entity_mention_context_crud.get_sentiment_trend(
        session, entity_id=entity_id, start_date=start_date, end_date=end_date
    )


@with_session
def get_articles_mentioning_entity(
    entity_id: int, start_date: datetime, end_date: datetime, *, session: Session
) -> List[Article]:
    """Get all articles mentioning an entity within a date range.
    
    Args:
        entity_id: ID of the entity
        start_date: Start date for the range
        end_date: End date for the range
        session: Database session
        
    Returns:
        List of articles mentioning the entity
    """
    from local_newsifier.crud.canonical_entity import canonical_entity as canonical_entity_crud
    from local_newsifier.models.pydantic_models import Article
    
    db_articles = canonical_entity_crud.get_articles_mentioning_entity(
        session, entity_id=entity_id, start_date=start_date, end_date=end_date
    )
    return [Article.model_validate(article) for article in db_articles]