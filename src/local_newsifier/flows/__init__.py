"""Flows for the local newsifier package."""

from .news_pipeline import NewsPipelineFlow
from .rss_scraping_flow import RSSScrapingFlow
from .analysis import HeadlineTrendFlow

__all__ = [
    "NewsPipelineFlow", 
    "RSSScrapingFlow",
    "HeadlineTrendFlow",
]