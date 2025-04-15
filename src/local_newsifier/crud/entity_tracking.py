"""CRUD operations for entity tracking models."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple

from sqlmodel import Session, select
from sqlalchemy import func, and_

from local_newsifier.models.entity_tracking import (
    CanonicalEntity,
    EntityMentionContext,
    EntityProfile,
    entity_mentions,
    entity_relationships,
)
from local_newsifier.models.article import Article


def create_canonical_entity(session: Session, entity_data: Dict[str, Any]) -> CanonicalEntity:
    """Create a new canonical entity in the database.
    
    Args:
        session: Database session
        entity_data: Canonical entity data dictionary
        
    Returns:
        Created canonical entity
    """
    db_entity = CanonicalEntity(**entity_data)
    session.add(db_entity)
    session.commit()
    session.refresh(db_entity)
    return db_entity


def get_canonical_entity(session: Session, entity_id: int) -> Optional[CanonicalEntity]:
    """Get a canonical entity by ID.
    
    Args:
        session: Database session
        entity_id: ID of the canonical entity to get
        
    Returns:
        Canonical entity if found, None otherwise
    """
    return session.get(CanonicalEntity, entity_id)


def get_canonical_entity_by_name(
    session: Session, name: str, entity_type: str
) -> Optional[CanonicalEntity]:
    """Get a canonical entity by name and type.
    
    Args:
        session: Database session
        name: Name of the canonical entity
        entity_type: Type of the entity (e.g., "PERSON")
        
    Returns:
        Canonical entity if found, None otherwise
    """
    statement = select(CanonicalEntity).where(
        CanonicalEntity.name == name,
        CanonicalEntity.entity_type == entity_type
    )
    return session.exec(statement).first()


def get_canonical_entities_by_type(session: Session, entity_type: str) -> List[CanonicalEntity]:
    """Get all canonical entities of a specific type.
    
    Args:
        session: Database session
        entity_type: Type of entities to get
        
    Returns:
        List of canonical entities of the specified type
    """
    statement = select(CanonicalEntity).where(
        CanonicalEntity.entity_type == entity_type
    )
    return session.exec(statement).all()


def get_all_canonical_entities(session: Session, entity_type: Optional[str] = None) -> List[CanonicalEntity]:
    """Get all canonical entities, optionally filtered by type.
    
    Args:
        session: Database session
        entity_type: Optional type to filter by
        
    Returns:
        List of canonical entities
    """
    statement = select(CanonicalEntity)
    if entity_type:
        statement = statement.where(CanonicalEntity.entity_type == entity_type)
    return session.exec(statement).all()


def add_entity_mention_context(
    session: Session, context_data: Dict[str, Any]
) -> EntityMentionContext:
    """Add context for an entity mention.
    
    Args:
        session: Database session
        context_data: Entity mention context data
        
    Returns:
        Created entity mention context
    """
    db_context = EntityMentionContext(**context_data)
    session.add(db_context)
    session.commit()
    session.refresh(db_context)
    return db_context


def add_entity_profile(session: Session, profile_data: Dict[str, Any]) -> EntityProfile:
    """Add a new entity profile.
    
    Args:
        session: Database session
        profile_data: Entity profile data
        
    Returns:
        Created entity profile
    """
    # Check if profile already exists
    statement = select(EntityProfile).where(
        EntityProfile.canonical_entity_id == profile_data["canonical_entity_id"],
        EntityProfile.profile_type == profile_data["profile_type"]
    )
    existing_profile = session.exec(statement).first()
    
    if existing_profile:
        raise ValueError(f"Profile already exists for entity {profile_data['canonical_entity_id']}")
        
    db_profile = EntityProfile(**profile_data)
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    return db_profile


def update_entity_profile(session: Session, profile_data: Dict[str, Any]) -> EntityProfile:
    """Update an entity profile.
    
    Args:
        session: Database session
        profile_data: Profile data to update
        
    Returns:
        Updated profile
    """
    # Get existing profile
    statement = select(EntityProfile).where(
        EntityProfile.canonical_entity_id == profile_data["canonical_entity_id"],
        EntityProfile.profile_type == profile_data["profile_type"]
    )
    db_profile = session.exec(statement).first()
    
    if db_profile:
        # Update profile fields
        db_profile.content = profile_data["content"]
        db_profile.profile_metadata = profile_data["profile_metadata"]
        db_profile.updated_at = datetime.now(timezone.utc)
        
        session.add(db_profile)
        session.commit()
        session.refresh(db_profile)
        return db_profile
    
    # If profile doesn't exist, create it
    return add_entity_profile(session, profile_data)


def get_entity_profile(session: Session, entity_id: int) -> Optional[EntityProfile]:
    """Get the profile for an entity.
    
    Args:
        session: Database session
        entity_id: ID of the entity
        
    Returns:
        Entity profile if found, None otherwise
    """
    statement = select(EntityProfile).where(
        EntityProfile.canonical_entity_id == entity_id
    )
    return session.exec(statement).first()


def get_entity_timeline(
    session: Session, entity_id: int, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    """Get the timeline of entity mentions.
    
    Args:
        session: Database session
        entity_id: ID of the entity
        start_date: Start date for the timeline
        end_date: End date for the timeline
        
    Returns:
        List of timeline entries
    """
    results = (
        session.query(
            Article.published_at,
            func.count(entity_mentions.c.id).label("mention_count"),
        )
        .join(entity_mentions, Article.id == entity_mentions.c.article_id)
        .filter(
            entity_mentions.c.canonical_entity_id == entity_id,
            Article.published_at >= start_date,
            Article.published_at <= end_date,
        )
        .group_by(Article.published_at)
        .order_by(Article.published_at)
        .all()
    )
    
    return [
        {
            "date": date,
            "mention_count": count,
        }
        for date, count in results
    ]


def get_entity_sentiment_trend(
    session: Session, entity_id: int, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    """Get the sentiment trend for an entity.
    
    Args:
        session: Database session
        entity_id: ID of the entity
        start_date: Start date for the trend
        end_date: End date for the trend
        
    Returns:
        List of sentiment trend entries
    """
    results = (
        session.query(
            Article.published_at,
            func.avg(EntityMentionContext.sentiment_score).label("avg_sentiment"),
        )
        .join(entity_mentions, Article.id == entity_mentions.c.article_id)
        .join(
            EntityMentionContext,
            EntityMentionContext.entity_id == entity_mentions.c.entity_id,
        )
        .filter(
            entity_mentions.c.canonical_entity_id == entity_id,
            Article.published_at >= start_date,
            Article.published_at <= end_date,
        )
        .group_by(Article.published_at)
        .order_by(Article.published_at)
        .all()
    )
    
    return [
        {
            "date": date,
            "avg_sentiment": float(sentiment) if sentiment is not None else None,
        }
        for date, sentiment in results
    ]


def get_articles_mentioning_entity(
    session: Session, entity_id: int, start_date: datetime, end_date: datetime
) -> List[Article]:
    """Get all articles mentioning an entity within a date range.
    
    Args:
        session: Database session
        entity_id: ID of the entity
        start_date: Start date for the range
        end_date: End date for the range
        
    Returns:
        List of articles mentioning the entity
    """
    statement = (
        select(Article)
        .join(entity_mentions, Article.id == entity_mentions.c.article_id)
        .where(
            entity_mentions.c.canonical_entity_id == entity_id,
            Article.published_at >= start_date,
            Article.published_at <= end_date,
        )
    )
    
    return session.exec(statement).all()