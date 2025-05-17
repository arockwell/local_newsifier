"""Dependency injection providers used across Local Newsifier.

This module defines lightweight factories for CRUD, tool, service, and command
providers. Each provider uses ``fastapi-injectable`` with ``use_cache=False`` to
ensure a fresh instance on every injection.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Callable, Dict, Generator, Optional

from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

logger = logging.getLogger(__name__)


@injectable(use_cache=False)
def get_session() -> Generator[Session, None, None]:
    """Yield a database session."""

    from local_newsifier.database.engine import get_session as get_db_session

    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()


def _create_crud_provider(module_path: str, attr_name: str) -> Callable[[], Any]:
    """Return a provider that imports ``attr_name`` from ``module_path``."""

    @injectable(use_cache=False)
    def provider():
        module = importlib.import_module(module_path)
        return getattr(module, attr_name)

    provider.__name__ = f"get_{attr_name}_crud"
    provider.__doc__ = f"Provide the {attr_name.replace('_', ' ')} CRUD component."
    return provider


_CRUD_SPECS: Dict[str, str] = {
    "article": "local_newsifier.crud.article",
    "entity": "local_newsifier.crud.entity",
    "entity_relationship": "local_newsifier.crud.entity_relationship",
    "rss_feed": "local_newsifier.crud.rss_feed",
    "analysis_result": "local_newsifier.crud.analysis_result",
    "canonical_entity": "local_newsifier.crud.canonical_entity",
    "entity_mention_context": "local_newsifier.crud.entity_mention_context",
    "entity_profile": "local_newsifier.crud.entity_profile",
    "feed_processing_log": "local_newsifier.crud.feed_processing_log",
    "apify_source_config": "local_newsifier.crud.apify_source_config",
}

for _name, _path in _CRUD_SPECS.items():
    globals()[f"get_{_name}_crud"] = _create_crud_provider(_path, _name)


@injectable(use_cache=False)
def get_nlp_model() -> Any:
    """Load the spaCy language model if available."""

    try:
        import spacy
        return spacy.load("en_core_web_lg")
    except (ImportError, OSError) as exc:  # pragma: no cover - missing spacy
        logger.warning("Failed to load NLP model: %s", exc)
        return None


@injectable(use_cache=False)
def get_sentiment_analyzer_config() -> Dict[str, str]:
    """Configuration for the sentiment analyzer tool."""

    return {"model_name": "en_core_web_sm"}


@injectable(use_cache=False)
def get_entity_resolver_config() -> Dict[str, float]:
    """Configuration for the entity resolver tool."""

    return {"similarity_threshold": 0.85}


@injectable(use_cache=False)
def get_web_scraper_tool() -> Any:
    """Instantiate the web scraper tool."""

    from local_newsifier.tools.web_scraper import WebScraperTool
    import requests

    session = requests.Session()
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    session.headers.update({"User-Agent": user_agent})
    return WebScraperTool(session=session, web_driver=None, user_agent=user_agent)


@injectable(use_cache=False)
def get_sentiment_analyzer_tool() -> Any:
    """Instantiate the sentiment analyzer tool."""

    from local_newsifier.tools.sentiment_analyzer import SentimentAnalyzer

    return SentimentAnalyzer(nlp_model=get_nlp_model())


@injectable(use_cache=False)
def get_sentiment_tracker_tool(session: Session = Depends(get_session)) -> Any:
    """Instantiate the sentiment tracker tool."""

    from local_newsifier.tools.sentiment_tracker import SentimentTracker

    return SentimentTracker(session_factory=lambda: session)


@injectable(use_cache=False)
def get_opinion_visualizer_tool(session: Session = Depends(get_session)) -> Any:
    """Instantiate the opinion visualizer tool."""

    from local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool

    return OpinionVisualizerTool(session=session)


@injectable(use_cache=False)
def get_trend_analyzer_config() -> Dict[str, str]:
    """Configuration for the trend analyzer tool."""

    return {"model_name": "en_core_web_lg"}


@injectable(use_cache=False)
def get_trend_analyzer_tool() -> Any:
    """Instantiate the trend analyzer tool."""

    from local_newsifier.tools.analysis.trend_analyzer import TrendAnalyzer

    return TrendAnalyzer(nlp_model=get_nlp_model())


@injectable(use_cache=False)
def get_trend_reporter_tool() -> Any:
    """Instantiate the trend reporter tool."""

    from local_newsifier.tools.trend_reporter import TrendReporter

    return TrendReporter(output_dir="trend_output")


@injectable(use_cache=False)
def get_context_analyzer_config() -> Dict[str, str]:
    """Configuration for the context analyzer tool."""

    return {"model_name": "en_core_web_lg"}


@injectable(use_cache=False)
def get_context_analyzer_tool() -> Any:
    """Instantiate the context analyzer tool."""

    from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer

    return ContextAnalyzer(nlp_model=get_nlp_model())


@injectable(use_cache=False)
def get_entity_extractor() -> Any:
    """Instantiate the entity extractor tool."""

    from local_newsifier.tools.extraction.entity_extractor import EntityExtractor

    return EntityExtractor()


@injectable(use_cache=False)
def get_entity_extractor_tool() -> Any:
    """Alias for ``get_entity_extractor``."""

    return get_entity_extractor()


@injectable(use_cache=False)
def get_entity_resolver(config: Dict = Depends(get_entity_resolver_config)) -> Any:
    """Instantiate the entity resolver tool."""

    from local_newsifier.tools.resolution.entity_resolver import EntityResolver

    return EntityResolver(similarity_threshold=config["similarity_threshold"])


@injectable(use_cache=False)
def get_entity_resolver_tool() -> Any:
    """Alias for ``get_entity_resolver``."""

    return get_entity_resolver()


@injectable(use_cache=False)
def get_rss_parser_config() -> Dict[str, Any]:
    """Configuration for the RSS parser tool."""

    return {
        "cache_dir": "cache",
        "request_timeout": 30,
        "user_agent": "Local Newsifier RSS Parser",
    }


@injectable(use_cache=False)
def get_rss_parser(config: Dict = Depends(get_rss_parser_config)) -> Any:
    """Instantiate the RSS parser tool."""

    from local_newsifier.tools.rss_parser import RSSParser

    return RSSParser(
        cache_dir=config["cache_dir"],
        request_timeout=config["request_timeout"],
        user_agent=config["user_agent"],
    )


@injectable(use_cache=False)
def get_file_writer_config() -> Dict[str, str]:
    """Configuration for the file writer tool."""

    return {"output_dir": "output"}


@injectable(use_cache=False)
def get_file_writer_tool(config: Dict = Depends(get_file_writer_config)) -> Any:
    """Instantiate the file writer tool."""

    from local_newsifier.tools.file_writer import FileWriterTool

    return FileWriterTool(output_dir=config["output_dir"])


@injectable(use_cache=False)
def get_entity_service(
    entity_crud=Depends(lambda: get_entity_crud()),
    canonical_entity_crud=Depends(lambda: get_canonical_entity_crud()),
    entity_mention_context_crud=Depends(lambda: get_entity_mention_context_crud()),
    entity_profile_crud=Depends(lambda: get_entity_profile_crud()),
    article_crud=Depends(lambda: get_article_crud()),
    entity_extractor=Depends(get_entity_extractor),
    context_analyzer=Depends(get_context_analyzer_tool),
    entity_resolver=Depends(get_entity_resolver),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the entity service."""

    from local_newsifier.services.entity_service import EntityService

    return EntityService(
        entity_crud=entity_crud,
        canonical_entity_crud=canonical_entity_crud,
        entity_mention_context_crud=entity_mention_context_crud,
        entity_profile_crud=entity_profile_crud,
        article_crud=article_crud,
        entity_extractor=entity_extractor,
        context_analyzer=context_analyzer,
        entity_resolver=entity_resolver,
        session=session,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_entity_tracker_tool(
    entity_service=Depends(get_entity_service),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the entity tracker tool."""

    from local_newsifier.tools.entity_tracker_service import EntityTracker

    return EntityTracker(entity_service=entity_service, session=session)


@injectable(use_cache=False)
def get_apify_service() -> Any:
    """Instantiate the Apify service."""

    from local_newsifier.services.apify_service import ApifyService

    return ApifyService()


@injectable(use_cache=False)
def get_apify_schedule_manager(
    apify_service=Depends(get_apify_service),
    apify_source_config_crud=Depends(lambda: get_apify_source_config_crud()),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the Apify schedule manager service."""

    from local_newsifier.services.apify_schedule_manager import ApifyScheduleManager

    return ApifyScheduleManager(
        apify_service=apify_service,
        apify_source_config_crud=apify_source_config_crud,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_apify_source_config_service(
    apify_source_config_crud=Depends(lambda: get_apify_source_config_crud()),
    apify_service=Depends(get_apify_service),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the Apify source config service."""

    from local_newsifier.services.apify_source_config_service import (
        ApifySourceConfigService,
    )

    return ApifySourceConfigService(
        apify_source_config_crud=apify_source_config_crud,
        apify_service=apify_service,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_analysis_service(
    analysis_result_crud=Depends(lambda: get_analysis_result_crud()),
    article_crud=Depends(lambda: get_article_crud()),
    entity_crud=Depends(lambda: get_entity_crud()),
    trend_analyzer=Depends(get_trend_analyzer_tool),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the analysis service."""

    from local_newsifier.services.analysis_service import AnalysisService

    return AnalysisService(
        analysis_result_crud=analysis_result_crud,
        article_crud=article_crud,
        entity_crud=entity_crud,
        trend_analyzer=trend_analyzer,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_article_service(
    article_crud=Depends(lambda: get_article_crud()),
    analysis_result_crud=Depends(lambda: get_analysis_result_crud()),
    entity_service=Depends(get_entity_service),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the article service."""

    from local_newsifier.services.article_service import ArticleService

    return ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        entity_service=entity_service,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_news_pipeline_service(
    article_service=Depends(get_article_service),
    web_scraper=Depends(get_web_scraper_tool),
    file_writer=Depends(get_file_writer_tool),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the news pipeline service."""

    from local_newsifier.services.news_pipeline_service import NewsPipelineService

    return NewsPipelineService(
        article_service=article_service,
        web_scraper=web_scraper,
        file_writer=file_writer,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_rss_feed_service(
    rss_feed_crud=Depends(lambda: get_rss_feed_crud()),
    feed_processing_log_crud=Depends(lambda: get_feed_processing_log_crud()),
    article_service=Depends(get_article_service),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the RSS feed service."""

    from local_newsifier.services.rss_feed_service import RSSFeedService

    return RSSFeedService(
        rss_feed_crud=rss_feed_crud,
        feed_processing_log_crud=feed_processing_log_crud,
        article_service=article_service,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_entity_tracking_flow(
    entity_service=Depends(get_entity_service),
    entity_tracker=Depends(get_entity_tracker_tool),
    entity_extractor=Depends(get_entity_extractor_tool),
    context_analyzer=Depends(get_context_analyzer_tool),
    entity_resolver=Depends(get_entity_resolver_tool),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the entity tracking flow."""

    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow

    return EntityTrackingFlow(
        entity_service=entity_service,
        entity_tracker=entity_tracker,
        entity_extractor=entity_extractor,
        context_analyzer=context_analyzer,
        entity_resolver=entity_resolver,
        session=session,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_headline_trend_flow(
    analysis_service=Depends(get_analysis_service),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the headline trend flow."""

    from local_newsifier.flows.analysis.headline_trend_flow import HeadlineTrendFlow

    return HeadlineTrendFlow(analysis_service=analysis_service, session=session)


@injectable(use_cache=False)
def get_rss_scraping_flow(
    rss_feed_service=Depends(get_rss_feed_service),
    article_service=Depends(get_article_service),
    rss_parser=Depends(get_rss_parser),
    web_scraper=Depends(get_web_scraper_tool),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the RSS scraping flow."""

    from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow

    return RSSScrapingFlow(
        rss_feed_service=rss_feed_service,
        article_service=article_service,
        rss_parser=rss_parser,
        web_scraper=web_scraper,
        cache_dir="cache",
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_news_pipeline_flow(
    article_service=Depends(get_article_service),
    entity_service=Depends(get_entity_service),
    pipeline_service=Depends(get_news_pipeline_service),
    web_scraper=Depends(get_web_scraper_tool),
    file_writer=Depends(get_file_writer_tool),
    entity_extractor=Depends(get_entity_extractor_tool),
    context_analyzer=Depends(get_context_analyzer_tool),
    entity_resolver=Depends(get_entity_resolver_tool),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the news pipeline flow."""

    from local_newsifier.flows.news_pipeline import NewsPipelineFlow

    return NewsPipelineFlow(
        article_service=article_service,
        entity_service=entity_service,
        pipeline_service=pipeline_service,
        web_scraper=web_scraper,
        file_writer=file_writer,
        entity_extractor=entity_extractor,
        context_analyzer=context_analyzer,
        entity_resolver=entity_resolver,
        session=session,
        session_factory=lambda: session,
    )


@injectable(use_cache=False)
def get_trend_analysis_flow(
    analysis_service=Depends(get_analysis_service),
    trend_reporter=Depends(get_trend_reporter_tool),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the trend analysis flow."""

    from local_newsifier.flows.trend_analysis_flow import NewsTrendAnalysisFlow
    from local_newsifier.models.trend import TrendAnalysisConfig

    return NewsTrendAnalysisFlow(
        analysis_service=analysis_service,
        trend_reporter=trend_reporter,
        session=session,
        config=TrendAnalysisConfig(),
    )


@injectable(use_cache=False)
def get_public_opinion_flow(
    sentiment_analyzer=Depends(get_sentiment_analyzer_tool),
    sentiment_tracker=Depends(get_sentiment_tracker_tool),
    opinion_visualizer=Depends(get_opinion_visualizer_tool),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the public opinion flow."""

    from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow

    return PublicOpinionFlow(
        sentiment_analyzer=sentiment_analyzer,
        sentiment_tracker=sentiment_tracker,
        opinion_visualizer=opinion_visualizer,
        session=session,
    )


def _create_cli_provider(path: str) -> Callable[[], Any]:
    """Create a provider returning a CLI command function."""

    module_path, func_name = path.rsplit(".", 1)

    @injectable(use_cache=False)
    def provider():
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    provider.__name__ = f"get_{func_name}_command"
    provider.__doc__ = f"Provide the {func_name} command function."
    return provider


_CLI_SPECS = {
    "db_stats": "local_newsifier.cli.commands.db.db_stats",
    "db_duplicates": "local_newsifier.cli.commands.db.check_duplicates",
    "db_articles": "local_newsifier.cli.commands.db.list_articles",
    "db_inspect": "local_newsifier.cli.commands.db.inspect_record",
    "feeds_list": "local_newsifier.cli.commands.feeds.list_feeds",
    "feeds_add": "local_newsifier.cli.commands.feeds.add_feed",
    "feeds_show": "local_newsifier.cli.commands.feeds.show_feed",
    "feeds_process": "local_newsifier.cli.commands.feeds.process_feed",
}

for _name, _path in _CLI_SPECS.items():
    globals()[f"get_{_name}_command"] = _create_cli_provider(_path)


@injectable(use_cache=False)
def get_injectable_entity_tracker(
    entity_service=Depends(get_entity_service),
    session: Session = Depends(get_session),
) -> Any:
    """Instantiate the entity tracker tool for CLI usage."""

    from local_newsifier.tools.entity_tracker_service import EntityTracker

    return EntityTracker(entity_service=entity_service, session=session)


@injectable(use_cache=False)
def get_apify_service_cli(token: Optional[str] = None) -> Any:
    """Instantiate the Apify service for CLI commands."""

    from local_newsifier.services.apify_service import ApifyService

    return ApifyService(token=token)

