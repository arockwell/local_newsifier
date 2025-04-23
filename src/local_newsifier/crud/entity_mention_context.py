"""CRUD operations for entity mention contexts."""

from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select, func

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.article import Article
from local_newsifier.models.entity_tracking import EntityMentionContext, EntityMention


class CRUDEntityMentionContext(CRUDBase[EntityMentionContext]):
    """CRUD operations for entity mention contexts."""

    def get_by_entity_and_article(
        self, db: Session, *, entity_id: int, article_id: int
    ) -> Optional[EntityMentionContext]:
        """Get context for an entity in an article.

        Args:
            db: Database session
            entity_id: ID of the entity
            article_id: ID of the article

        Returns:
            Entity mention context if found, None otherwise
        """
        result = db.execute(select(EntityMentionContext).where(
            EntityMentionContext.entity_id == entity_id,
            EntityMentionContext.article_id == article_id
        )).first()
        return result[0] if result else None

    def get_by_entity(
        self, db: Session, *, entity_id: int
    ) -> List[EntityMentionContext]:
        """Get all contexts for an entity.

        Args:
            db: Database session
            entity_id: ID of the entity

        Returns:
            List of entity mention contexts
        """
        results = db.execute(select(EntityMentionContext).where(
            EntityMentionContext.entity_id == entity_id
        )).all()
        return [row[0] for row in results]

    def get_sentiment_trend(
        self,
        db: Session,
        *,
        entity_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """Get the sentiment trend for an entity.

        Args:
            db: Database session
            entity_id: ID of the entity
            start_date: Start date for the trend
            end_date: End date for the trend

        Returns:
            List of sentiment trend entries
        """
        statement = select(
            Article.published_at,
            func.avg(EntityMentionContext.sentiment_score).label("avg_sentiment")
        ).join(
            EntityMention, Article.id == EntityMention.article_id
        ).join(
            EntityMentionContext,
            EntityMentionContext.entity_id == EntityMention.entity_id
        ).where(
            EntityMention.canonical_entity_id == entity_id,
            Article.published_at >= start_date,
            Article.published_at <= end_date
        ).group_by(
            Article.published_at
        ).order_by(
            Article.published_at
        )
        
        results = db.execute(statement)
        
        return [
            {
                "date": date,
                "avg_sentiment": float(sentiment) if sentiment is not None else None,
            }
            for date, sentiment in results
        ]


entity_mention_context = CRUDEntityMentionContext(EntityMentionContext)
