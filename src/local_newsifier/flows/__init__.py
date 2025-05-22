"""Flows for the local newsifier package."""

from .analysis import HeadlineTrendFlow
from .news_pipeline import NewsPipelineFlow
from .rss_scraping_flow import RSSScrapingFlow

__all__ = [
    "NewsPipelineFlow",
    "RSSScrapingFlow",
    "HeadlineTrendFlow",
]
