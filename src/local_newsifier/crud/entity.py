"""CRUD operations for Entity model."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlmodel import Session, select

from local_newsifier.models.entity import Entity


def create_entity(session: Session, entity_data: Dict[str, Any]) -> Entity:
    """Create a new entity in the database.
    
    Args:
        session: Database session
        entity_data: Entity data dictionary
        
    Returns:
        Created entity
    """
    db_entity = Entity(**entity_data)
    session.add(db_entity)
    session.commit()
    session.refresh(db_entity)
    return db_entity


def get_entity(session: Session, entity_id: int) -> Optional[Entity]:
    """Get an entity by ID.
    
    Args:
        session: Database session
        entity_id: ID of the entity to get
        
    Returns:
        Entity if found, None otherwise
    """
    return session.get(Entity, entity_id)


def get_entities_by_type(session: Session, entity_type: str) -> List[Entity]:
    """Get all entities of a specific type.
    
    Args:
        session: Database session
        entity_type: Type of entities to get
        
    Returns:
        List of entities of the specified type
    """
    statement = select(Entity).where(Entity.entity_type == entity_type)
    return session.exec(statement).all()


def get_entities_by_article_and_type(
    session: Session, article_id: int, entity_type: str
) -> List[Entity]:
    """Get entities for an article of a specific type.
    
    Args:
        session: Database session
        article_id: ID of the article
        entity_type: Type of entities to get
        
    Returns:
        List of entities for the article of the specified type
    """
    statement = select(Entity).where(
        Entity.article_id == article_id,
        Entity.entity_type == entity_type
    )
    return session.exec(statement).all()


def delete_entity(session: Session, entity_id: int) -> bool:
    """Delete an entity from the database.
    
    Args:
        session: Database session
        entity_id: ID of the entity to delete
        
    Returns:
        True if entity was deleted, False otherwise
    """
    entity = session.get(Entity, entity_id)
    if entity:
        session.delete(entity)
        session.commit()
        return True
    return False