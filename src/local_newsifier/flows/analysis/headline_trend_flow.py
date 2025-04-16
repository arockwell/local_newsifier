"""
Flow for analyzing headline trends in news articles.

This module provides a crew.ai Flow for orchestrating headline trend analysis, including:

1. Managing database connections for retrieving news articles
2. Analyzing trends in headlines over specified time periods
3. Generating formatted reports of analysis results
4. Supporting different time intervals (daily, weekly, monthly)
5. Providing both date range and recent history analysis options

The HeadlineTrendFlow handles database session management, tool initialization,
and report generation in various formats (text, markdown, HTML).
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from crewai import Flow
from sqlalchemy.orm import Session

from ...database.adapter import with_session
from ...database.engine import get_session
from ...tools.analysis.headline_analyzer import HeadlineTrendAnalyzer

logger = logging.getLogger(__name__)


class HeadlineTrendFlow(Flow):
    """Flow for analyzing trends in article headlines over time."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the headline trend analysis flow.

        Args:
            session: Optional SQLAlchemy session to use
        """
        super().__init__()

        # Set up database connection if not provided
        if session is None:
            self.session_generator = get_session()
            self.session = next(self.session_generator)
            self._owns_session = True
        else:
            self.session = session
            self._owns_session = False

        # Initialize tools
        self.headline_analyzer = HeadlineTrendAnalyzer(self.session)

    def __del__(self):
        """Clean up resources when the flow is deleted."""
        if hasattr(self, "_owns_session") and self._owns_session:
            if hasattr(self, "session") and self.session is not None:
                try:
                    next(self.session_generator, None)
                except StopIteration:
                    pass

    def analyze_recent_trends(
        self, days_back: int = 30, interval: str = "day", top_n: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze headline trends over the recent past.

        Args:
            days_back: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            top_n: Number of top keywords to analyze per period

        Returns:
            Dictionary containing trend analysis results
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        logger.info(f"Analyzing headline trends from {start_date} to {end_date}")

        results = self.headline_analyzer.analyze_trends(
            start_date=start_date,
            end_date=end_date,
            time_interval=interval,
            top_n=top_n,
            session=self.session
        )

        return results

    def analyze_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
        top_n: int = 20,
    ) -> Dict[str, Any]:
        """
        Analyze headline trends for a specific date range.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            interval: Time interval for grouping ('day', 'week', 'month')
            top_n: Number of top keywords to analyze per period

        Returns:
            Dictionary containing trend analysis results
        """
        logger.info(f"Analyzing headline trends from {start_date} to {end_date}")

        results = self.headline_analyzer.analyze_trends(
            start_date=start_date,
            end_date=end_date,
            time_interval=interval,
            top_n=top_n,
            session=self.session
        )

        return results

    def generate_report(
        self, results: Dict[str, Any], format_type: str = "text"
    ) -> str:
        """
        Generate a formatted report from trend analysis results.

        Args:
            results: Trend analysis results from analyze_trends method
            format_type: Report format type ('text', 'markdown', 'html')

        Returns:
            Formatted report string
        """
        if "error" in results:
            return f"Error: {results['error']}"

        if format_type == "markdown":
            return self._generate_markdown_report(results)
        elif format_type == "html":
            return self._generate_html_report(results)
        else:
            return self._generate_text_report(results)

    def _generate_text_report(self, results: Dict[str, Any]) -> str:
        """Generate a plain text report."""
        report = "HEADLINE TREND ANALYSIS REPORT\n"
        report += "==============================\n\n"

        # Add trending terms
        report += "TOP TRENDING TERMS:\n"
        for i, term in enumerate(results.get("trending_terms", [])[:10], 1):
            growth = term["growth_rate"] * 100
            report += f"{i}. {term['term']} (Growth: {growth:.1f}%, Mentions: {term['total_mentions']})\n"

        report += "\nOVERALL TOP TERMS:\n"
        for i, (term, count) in enumerate(results.get("overall_top_terms", [])[:10], 1):
            report += f"{i}. {term} ({count} mentions)\n"

        report += "\nARTICLE COUNTS BY PERIOD:\n"
        for period, count in sorted(results.get("period_counts", {}).items()):
            report += f"{period}: {count} articles\n"

        return report

    def _generate_markdown_report(self, results: Dict[str, Any]) -> str:
        """Generate a markdown report."""
        report = "# Headline Trend Analysis Report\n\n"

        # Add trending terms
        report += "## Top Trending Terms\n\n"
        for i, term in enumerate(results.get("trending_terms", [])[:10], 1):
            growth = term["growth_rate"] * 100
            report += f"{i}. **{term['term']}** (Growth: {growth:.1f}%, Mentions: {term['total_mentions']})\n"

        report += "\n## Overall Top Terms\n\n"
        for i, (term, count) in enumerate(results.get("overall_top_terms", [])[:10], 1):
            report += f"{i}. **{term}** ({count} mentions)\n"

        report += "\n## Article Counts by Period\n\n"
        report += "| Period | Article Count |\n"
        report += "|--------|---------------|\n"
        for period, count in sorted(results.get("period_counts", {}).items()):
            report += f"| {period} | {count} |\n"

        return report

    def _generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate an HTML report."""
        report = (
            "<html><head><title>Headline Trend Analysis Report</title></head><body>\n"
        )
        report += "<h1>Headline Trend Analysis Report</h1>\n"

        # Add trending terms
        report += "<h2>Top Trending Terms</h2>\n<ol>\n"
        for term in results.get("trending_terms", [])[:10]:
            growth = term["growth_rate"] * 100
            report += f"<li><strong>{term['term']}</strong> (Growth: {growth:.1f}%, Mentions: {term['total_mentions']})</li>\n"
        report += "</ol>\n"

        report += "<h2>Overall Top Terms</h2>\n<ol>\n"
        for term, count in results.get("overall_top_terms", [])[:10]:
            report += f"<li><strong>{term}</strong> ({count} mentions)</li>\n"
        report += "</ol>\n"

        report += "<h2>Article Counts by Period</h2>\n"
        report += "<table border='1'>\n<tr><th>Period</th><th>Article Count</th></tr>\n"
        for period, count in sorted(results.get("period_counts", {}).items()):
            report += f"<tr><td>{period}</td><td>{count}</td></tr>\n"
        report += "</table>\n"

        report += "</body></html>"
        return report
