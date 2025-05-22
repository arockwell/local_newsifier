"""Model imports and initialization."""

# Re-export base SQLModel class
from sqlmodel import SQLModel

from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.apify import (ApifyCredentials, ApifyDatasetItem, ApifyJob,
                                          ApifySourceConfig, ApifyWebhook)
# Import all models from their original locations but don't re-export
# This prevents duplicate class registrations
from local_newsifier.models.article import Article
# Export table base
from local_newsifier.models.base import TableBase
from local_newsifier.models.entity import Entity
from local_newsifier.models.entity_tracking import (CanonicalEntity, EntityMention,
                                                    EntityMentionContext, EntityProfile,
                                                    EntityRelationship)
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog
from local_newsifier.models.sentiment import OpinionTrend, SentimentAnalysis, SentimentShift

# Export only the class names, not the actual classes
__all__ = [
    "SQLModel",
    "TableBase",
    "Article",
    "Entity",
    "AnalysisResult",
    "RSSFeed",
    "RSSFeedProcessingLog",
    # Entity tracking models
    "CanonicalEntity",
    "EntityMention",
    "EntityMentionContext",
    "EntityProfile",
    "EntityRelationship",
    # Sentiment models
    "SentimentAnalysis",
    "OpinionTrend",
    "SentimentShift",
    # Apify models
    "ApifySourceConfig",
    "ApifyJob",
    "ApifyDatasetItem",
    "ApifyCredentials",
    "ApifyWebhook",
]
