"""CRUD operations for entity mention contexts."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.entity_tracking import (EntityMentionContext,
                                                    EntityMentionContextCreate,
                                                    EntityMentionContextDB,
                                                    entity_mentions)


class CRUDEntityMentionContext(
    CRUDBase[
        EntityMentionContextDB,
        EntityMentionContextCreate,
        EntityMentionContext,
    ]
):
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
        db_context = (
            db.query(EntityMentionContextDB)
            .filter(
                EntityMentionContextDB.entity_id == entity_id,
                EntityMentionContextDB.article_id == article_id,
            )
            .first()
        )
        return (
            EntityMentionContext.model_validate(db_context)
            if db_context
            else None
        )

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
        db_contexts = (
            db.query(EntityMentionContextDB)
            .filter(EntityMentionContextDB.entity_id == entity_id)
            .all()
        )
        return [
            EntityMentionContext.model_validate(context)
            for context in db_contexts
        ]

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
        results = (
            db.query(
                ArticleDB.published_at,
                func.avg(EntityMentionContextDB.sentiment_score).label(
                    "avg_sentiment"
                ),
            )
            .join(
                entity_mentions, ArticleDB.id == entity_mentions.c.article_id
            )
            .join(
                EntityMentionContextDB,
                EntityMentionContextDB.entity_id
                == entity_mentions.c.entity_id,
            )
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                ArticleDB.published_at >= start_date,
                ArticleDB.published_at <= end_date,
            )
            .group_by(ArticleDB.published_at)
            .order_by(ArticleDB.published_at)
            .all()
        )

        return [
            {
                "date": date,
                "avg_sentiment": (
                    float(sentiment) if sentiment is not None else None
                ),
            }
            for date, sentiment in results
        ]


entity_mention_context = CRUDEntityMentionContext(
    EntityMentionContextDB, EntityMentionContext
)
