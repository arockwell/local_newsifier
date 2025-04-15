"""CRUD operations package."""

from local_newsifier.crud.article import (
    create_article,
    get_article,
    get_article_by_url,
    update_article_status,
    get_articles_by_status,
    get_articles_in_timeframe,
    get_entities_by_article,
    get_analysis_results_by_article,
)

from local_newsifier.crud.entity import (
    create_entity,
    get_entity,
    get_entities_by_type,
    get_entities_by_article_and_type,
    delete_entity,
)

from local_newsifier.crud.analysis_result import (
    create_analysis_result,
    get_analysis_result,
    get_results_by_type,
    get_results_by_article_and_type,
    delete_analysis_result,
)

from local_newsifier.crud.entity_tracking import (
    create_canonical_entity,
    get_canonical_entity,
    get_canonical_entity_by_name,
    get_canonical_entities_by_type,
    get_all_canonical_entities,
    add_entity_mention_context,
    add_entity_profile,
    update_entity_profile,
    get_entity_profile,
    get_entity_timeline,
    get_entity_sentiment_trend,
    get_articles_mentioning_entity,
)

__all__ = [
    # Article operations
    "create_article",
    "get_article",
    "get_article_by_url",
    "update_article_status",
    "get_articles_by_status",
    "get_articles_in_timeframe",
    "get_entities_by_article",
    "get_analysis_results_by_article",
    # Entity operations
    "create_entity",
    "get_entity",
    "get_entities_by_type",
    "get_entities_by_article_and_type",
    "delete_entity",
    # Analysis result operations
    "create_analysis_result",
    "get_analysis_result",
    "get_results_by_type",
    "get_results_by_article_and_type",
    "delete_analysis_result",
    # Entity tracking operations
    "create_canonical_entity",
    "get_canonical_entity",
    "get_canonical_entity_by_name",
    "get_canonical_entities_by_type",
    "get_all_canonical_entities",
    "add_entity_mention_context",
    "add_entity_profile",
    "update_entity_profile",
    "get_entity_profile",
    "get_entity_timeline",
    "get_entity_sentiment_trend",
    "get_articles_mentioning_entity",
]