"""Tool for visualizing sentiment and opinion data."""

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Optional, Tuple, Union

from fastapi import Depends, Query
from fastapi_injectable import injectable
from sqlmodel import Session, select

from local_newsifier.database.transaction import JoinTransactionMode

if TYPE_CHECKING:
    from local_newsifier.models.sentiment import SentimentVisualizationData
else:
    from local_newsifier.models.sentiment import SentimentVisualizationData

logger = logging.getLogger(__name__)


@injectable(use_cache=False)
class OpinionVisualizerTool:
    """Tool for generating visualizations of sentiment and opinion data.

    Uses use_cache=False to create new instances for each injection, as it
    interacts with database and maintains state during visualization generation.
    """

    def __init__(
        self,
        session: Annotated[Session, Depends(), Query(JoinTransactionMode.CONDITIONAL_SAVEPOINT)],
    ):
        """
        Initialize the opinion visualizer.

        Args:
            session: SQLModel session for database operations
                    Injected via FastAPI-Injectable dependency injection
                    With transaction mode set to CONDITIONAL_SAVEPOINT
        """
        # Store the session for instance-level usage
        self.session = session
        # Create a session factory for ease of use
        self.session_factory = lambda: session

    def prepare_timeline_data(
        self,
        topic: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
    ) -> SentimentVisualizationData:
        """
        Prepare data for a sentiment timeline visualization.

        Args:
            topic: Topic to visualize
            start_date: Start date for visualization
            end_date: End date for visualization
            interval: Time interval for grouping

        Returns:
            Sentiment visualization data
        """
        # Import necessary classes here to avoid circular imports
        from ..models.database.analysis_result import AnalysisResult
        from ..models.database.article import Article

        # Get analysis results for the topic using SQLModel syntax
        statement = (
            select(AnalysisResult)
            .where(
                AnalysisResult.analysis_type == "SENTIMENT",
                Article.published_at >= start_date,
                Article.published_at <= end_date,
            )
            .join(Article)
        )

        results = self.session.execute(statement)
        analysis_results = results.all()

        # Process results into time periods
        time_periods = []
        sentiment_values = []
        article_counts = []
        confidence_intervals = []

        # Group results by interval
        current_date = start_date
        while current_date <= end_date:
            next_date = current_date + timedelta(days=1)

            # Filter results for this period
            period_results = [
                r
                for r in analysis_results
                if current_date <= r.article.published_at < next_date
                and topic in r.results.get("topic_sentiments", {})
            ]

            if period_results:
                # Calculate average sentiment for this period
                sentiments = [r.results["topic_sentiments"][topic] for r in period_results]
                avg_sentiment = sum(sentiments) / len(sentiments)

                time_periods.append(current_date.strftime("%Y-%m-%d"))
                sentiment_values.append(avg_sentiment)
                article_counts.append(len(period_results))

                # Calculate confidence interval (95%)
                if len(period_results) > 1:
                    # Assuming standard deviation is 0.2 for simplicity
                    std_dev = 0.2
                    margin = 1.96 * std_dev / (len(period_results) ** 0.5)
                    confidence_intervals.append(
                        {
                            "lower": avg_sentiment - margin,
                            "upper": avg_sentiment + margin,
                        }
                    )
                else:
                    confidence_intervals.append(
                        {"lower": avg_sentiment - 0.2, "upper": avg_sentiment + 0.2}
                    )
            else:
                time_periods.append(current_date.strftime("%Y-%m-%d"))
                sentiment_values.append(0.0)
                article_counts.append(0)
                confidence_intervals.append({"lower": -0.2, "upper": 0.2})

            current_date = next_date

        return SentimentVisualizationData(
            topic=topic,
            time_periods=time_periods,
            sentiment_values=sentiment_values,
            confidence_intervals=confidence_intervals,
            article_counts=article_counts,
            viz_metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "interval": interval,
            },
        )

    def prepare_comparison_data(
        self,
        topics: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
    ) -> Dict[str, SentimentVisualizationData]:
        """
        Prepare data for comparative sentiment visualization.

        Args:
            topics: List of topics to compare
            start_date: Start date for visualization
            end_date: End date for visualization
            interval: Time interval for grouping

        Returns:
            Dictionary mapping topics to visualization data
        """
        comparison_data = {}

        for topic in topics:
            topic_data = self.prepare_timeline_data(topic, start_date, end_date, interval)
            comparison_data[topic] = topic_data

        return comparison_data

    def generate_text_report(
        self,
        visualization_data: Union[
            SentimentVisualizationData, Dict[str, SentimentVisualizationData]
        ],
        report_type: str = "timeline",
    ) -> str:
        """
        Generate a text report from visualization data.

        Args:
            visualization_data: Sentiment visualization data
            report_type: Type of report ("timeline" or "comparison")

        Returns:
            Formatted text report
        """
        if report_type == "timeline" and isinstance(visualization_data, SentimentVisualizationData):
            return self._generate_timeline_text_report(visualization_data)
        elif report_type == "comparison" and isinstance(visualization_data, dict):
            return self._generate_comparison_text_report(visualization_data)
        else:
            raise ValueError(f"Invalid report type: {report_type} or data type mismatch")

    def generate_markdown_report(
        self,
        visualization_data: Union[
            SentimentVisualizationData, Dict[str, SentimentVisualizationData]
        ],
        report_type: str = "timeline",
    ) -> str:
        """
        Generate a markdown report from visualization data.

        Args:
            visualization_data: Sentiment visualization data
            report_type: Type of report ("timeline" or "comparison")

        Returns:
            Formatted markdown report
        """
        if report_type == "timeline" and isinstance(visualization_data, SentimentVisualizationData):
            return self._generate_timeline_markdown_report(visualization_data)
        elif report_type == "comparison" and isinstance(visualization_data, dict):
            return self._generate_comparison_markdown_report(visualization_data)
        else:
            raise ValueError(f"Invalid report type: {report_type} or data type mismatch")

    def generate_html_report(
        self,
        visualization_data: Union[
            SentimentVisualizationData, Dict[str, SentimentVisualizationData]
        ],
        report_type: str = "timeline",
    ) -> str:
        """
        Generate an HTML report from visualization data.

        Args:
            visualization_data: Sentiment visualization data
            report_type: Type of report ("timeline" or "comparison")

        Returns:
            Formatted HTML report
        """
        if report_type == "timeline" and isinstance(visualization_data, SentimentVisualizationData):
            return self._generate_timeline_html_report(visualization_data)
        elif report_type == "comparison" and isinstance(visualization_data, dict):
            return self._generate_comparison_html_report(visualization_data)
        else:
            raise ValueError(f"Invalid report type: {report_type} or data type mismatch")

    def _timeline_summary(self, data: SentimentVisualizationData) -> Dict[str, Any]:
        """Return summary statistics for a timeline visualization."""
        avg_sentiment = sum(data.sentiment_values) / len(data.sentiment_values)
        return {
            "avg_sentiment": avg_sentiment,
            "min_sentiment": min(data.sentiment_values),
            "max_sentiment": max(data.sentiment_values),
            "total_articles": sum(data.article_counts),
            "viz_metadata": data.viz_metadata or {},
        }

    def _comparison_summary(
        self, data: Dict[str, SentimentVisualizationData]
    ) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any]]:
        """Return summary statistics for comparison visualizations."""
        if not data:
            return {}, {}

        topic_stats = {}
        for topic, topic_data in data.items():
            if not topic_data.sentiment_values:
                continue
            topic_stats[topic] = {
                "avg_sentiment": sum(topic_data.sentiment_values)
                / len(topic_data.sentiment_values),
                "total_articles": sum(topic_data.article_counts),
            }

        first_topic = list(data.keys())[0]
        viz_metadata = data[first_topic].viz_metadata or {}

        return topic_stats, viz_metadata

    def _generate_timeline_text_report(self, data: SentimentVisualizationData) -> str:
        """Generate a text report for timeline visualization."""
        # Calculate summary statistics
        if not data.sentiment_values:
            return f"No sentiment data available for topic: {data.topic}"

        summary = self._timeline_summary(data)

        # Build report
        report = f"SENTIMENT ANALYSIS REPORT: {data.topic}\n"
        report += "=" * 50 + "\n\n"

        # Check if metadata is available
        metadata = summary["viz_metadata"]
        if (
            metadata
            and "start_date" in metadata
            and "end_date" in metadata
            and "interval" in metadata
        ):
            report += f"Time period: {metadata['start_date']} to {metadata['end_date']}\n"
            report += f"Interval: {metadata['interval']}\n\n"
        else:
            # Fallback to basic information
            report += "Time period: Not specified\n"
            report += "Interval: Not specified\n\n"

        report += "SUMMARY STATISTICS\n"
        report += f"Average sentiment: {summary['avg_sentiment']:.2f}\n"
        report += f"Minimum sentiment: {summary['min_sentiment']:.2f}\n"
        report += f"Maximum sentiment: {summary['max_sentiment']:.2f}\n"
        report += f"Total articles: {summary['total_articles']}\n\n"

        report += "SENTIMENT TIMELINE\n"
        for i, period in enumerate(data.time_periods):
            sentiment = data.sentiment_values[i]
            articles = data.article_counts[i]
            report += f"{period}: {sentiment:.2f} ({articles} articles)\n"

        return report

    def _generate_comparison_text_report(self, data: Dict[str, SentimentVisualizationData]) -> str:
        """Generate a text report for comparison visualization."""
        if not data:
            return "No sentiment data available for comparison"

        # Build report
        report = "SENTIMENT COMPARISON REPORT\n"
        report += "=" * 50 + "\n\n"

        topic_stats, viz_metadata = self._comparison_summary(data)

        if (
            viz_metadata
            and "start_date" in viz_metadata
            and "end_date" in viz_metadata
            and "interval" in viz_metadata
        ):
            report += f"Time period: {viz_metadata['start_date']} to {viz_metadata['end_date']}\n"
            report += f"Interval: {viz_metadata['interval']}\n\n"
        else:
            report += "Time period: Not specified\n"
            report += "Interval: Not specified\n\n"

        report += "SUMMARY STATISTICS\n"
        for topic, stats in topic_stats.items():
            report += (
                f"{topic}: {stats['avg_sentiment']:.2f} ({stats['total_articles']} articles)\n"
            )

        report += "\nDETAILED COMPARISON\n"

        # Get all unique periods across all topics
        all_periods = set()
        for topic_data in data.values():
            all_periods.update(topic_data.time_periods)

        # Sort periods
        sorted_periods = sorted(all_periods)

        # Create a table of values
        for period in sorted_periods:
            report += f"\n{period}:\n"
            for topic, topic_data in data.items():
                try:
                    idx = topic_data.time_periods.index(period)
                    sentiment = topic_data.sentiment_values[idx]
                    articles = topic_data.article_counts[idx]
                    report += f"  {topic}: {sentiment:.2f} ({articles} articles)\n"
                except ValueError:
                    report += f"  {topic}: No data\n"

        return report

    def _generate_timeline_markdown_report(self, data: SentimentVisualizationData) -> str:
        """Generate a markdown report for timeline visualization."""
        # Calculate summary statistics
        if not data.sentiment_values:
            return f"No sentiment data available for topic: {data.topic}"

        summary = self._timeline_summary(data)

        # Build report
        report = f"# Sentiment Analysis Report: {data.topic}\n\n"

        # Check if metadata is available
        metadata = summary["viz_metadata"]
        if (
            metadata
            and "start_date" in metadata
            and "end_date" in metadata
            and "interval" in metadata
        ):
            report += f"**Time period:** {metadata['start_date']} to {metadata['end_date']}  \n"
            report += f"**Interval:** {metadata['interval']}\n\n"
        else:
            # Fallback to basic information
            report += "**Time period:** Not specified  \n"
            report += "**Interval:** Not specified\n\n"

        report += "## Summary Statistics\n\n"
        report += f"- **Average sentiment:** {summary['avg_sentiment']:.2f}\n"
        report += f"- **Minimum sentiment:** {summary['min_sentiment']:.2f}\n"
        report += f"- **Maximum sentiment:** {summary['max_sentiment']:.2f}\n"
        report += f"- **Total articles:** {summary['total_articles']}\n\n"

        report += "## Sentiment Timeline\n\n"
        report += "| Period | Sentiment | Articles |\n"
        report += "|--------|-----------|----------|\n"
        for i, period in enumerate(data.time_periods):
            sentiment = data.sentiment_values[i]
            articles = data.article_counts[i]
            report += f"| {period} | {sentiment:.2f} | {articles} |\n"

        return report

    def _generate_comparison_markdown_report(
        self, data: Dict[str, SentimentVisualizationData]
    ) -> str:
        """Generate a markdown report for comparison visualization."""
        if not data:
            return "No sentiment data available for comparison"

        # Build report
        report = "# Sentiment Comparison Report\n\n"

        topic_stats, viz_metadata = self._comparison_summary(data)

        if (
            viz_metadata
            and "start_date" in viz_metadata
            and "end_date" in viz_metadata
            and "interval" in viz_metadata
        ):
            report += (
                f"**Time period:** {viz_metadata['start_date']} to {viz_metadata['end_date']}  \n"
            )
            report += f"**Interval:** {viz_metadata['interval']}\n\n"
        else:
            report += "**Time period:** Not specified  \n"
            report += "**Interval:** Not specified\n\n"

        report += "## Summary Statistics\n\n"
        report += "| Topic | Average Sentiment | Total Articles |\n"
        report += "|-------|------------------|----------------|\n"
        for topic, stats in topic_stats.items():
            report += f"| {topic} | {stats['avg_sentiment']:.2f} | {stats['total_articles']} |\n"

        report += "\n## Detailed Comparison\n\n"

        # Get all unique periods across all topics
        all_periods = set()
        for topic_data in data.values():
            all_periods.update(topic_data.time_periods)

        # Sort periods
        sorted_periods = sorted(all_periods)

        # Create header row with all topics
        report += "| Period |"
        for topic in data.keys():
            report += f" {topic} |"
        report += "\n"

        # Add separator row
        report += "|--------|"
        for _ in data.keys():
            report += "---------------|"
        report += "\n"

        # Add data rows
        for period in sorted_periods:
            report += f"| {period} |"
            for topic, topic_data in data.items():
                try:
                    idx = topic_data.time_periods.index(period)
                    sentiment = topic_data.sentiment_values[idx]
                    report += f" {sentiment:.2f} |"
                except ValueError:
                    report += " N/A |"
            report += "\n"

        return report

    def _generate_timeline_html_report(self, data: SentimentVisualizationData) -> str:
        """Generate an HTML report for timeline visualization."""
        # Calculate summary statistics
        if not data.sentiment_values:
            return f"<p>No sentiment data available for topic: {data.topic}</p>"

        summary = self._timeline_summary(data)

        # Build report
        report = "<html><head>\n"
        report += "<style>\n"
        report += "body { font-family: Arial, sans-serif; margin: 20px; }\n"
        report += "h1, h2 { color: #333; }\n"
        report += "table { border-collapse: collapse; width: 100%; }\n"
        report += "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n"
        report += "th { background-color: #f2f2f2; }\n"
        report += "tr:nth-child(even) { background-color: #f9f9f9; }\n"
        report += "</style>\n"
        report += f"<title>Sentiment Analysis: {data.topic}</title>\n"
        report += "</head><body>\n"

        report += f"<h1>Sentiment Analysis Report: {data.topic}</h1>\n"

        # Check if metadata is available
        metadata = summary["viz_metadata"]
        if (
            metadata
            and "start_date" in metadata
            and "end_date" in metadata
            and "interval" in metadata
        ):
            report += f"<p><strong>Time period:</strong> {metadata['start_date']} to {metadata['end_date']}<br>\n"
            report += f"<strong>Interval:</strong> {metadata['interval']}</p>\n"
        else:
            # Fallback to basic information
            report += "<p><strong>Time period:</strong> Not specified<br>\n"
            report += "<strong>Interval:</strong> Not specified</p>\n"

        report += "<h2>Summary Statistics</h2>\n"
        report += "<ul>\n"
        report += f"<li><strong>Average sentiment:</strong> {summary['avg_sentiment']:.2f}</li>\n"
        report += f"<li><strong>Minimum sentiment:</strong> {summary['min_sentiment']:.2f}</li>\n"
        report += f"<li><strong>Maximum sentiment:</strong> {summary['max_sentiment']:.2f}</li>\n"
        report += f"<li><strong>Total articles:</strong> {summary['total_articles']}</li>\n"
        report += "</ul>\n"

        report += "<h2>Sentiment Timeline</h2>\n"
        report += "<table>\n"
        report += "<tr><th>Period</th><th>Sentiment</th><th>Articles</th></tr>\n"
        for i, period in enumerate(data.time_periods):
            sentiment = data.sentiment_values[i]
            articles = data.article_counts[i]
            report += f"<tr><td>{period}</td><td>{sentiment:.2f}</td><td>{articles}</td></tr>\n"
        report += "</table>\n"

        report += "</body></html>"
        return report

    def _generate_comparison_html_report(self, data: Dict[str, SentimentVisualizationData]) -> str:
        """Generate an HTML report for comparison visualization."""
        if not data:
            return "<p>No sentiment data available for comparison</p>"

        # Build report
        report = "<html><head>\n"
        report += "<style>\n"
        report += "body { font-family: Arial, sans-serif; margin: 20px; }\n"
        report += "h1, h2 { color: #333; }\n"
        report += "table { border-collapse: collapse; width: 100%; }\n"
        report += "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }\n"
        report += "th { background-color: #f2f2f2; }\n"
        report += "tr:nth-child(even) { background-color: #f9f9f9; }\n"
        report += "</style>\n"
        report += "<title>Sentiment Comparison</title>\n"
        report += "</head><body>\n"

        report += "<h1>Sentiment Comparison Report</h1>\n"

        topic_stats, viz_metadata = self._comparison_summary(data)

        if (
            viz_metadata
            and "start_date" in viz_metadata
            and "end_date" in viz_metadata
            and "interval" in viz_metadata
        ):
            report += f"<p><strong>Time period:</strong> {viz_metadata['start_date']} to {viz_metadata['end_date']}<br>\n"
            report += f"<strong>Interval:</strong> {viz_metadata['interval']}</p>\n"
        else:
            report += "<p><strong>Time period:</strong> Not specified<br>\n"
            report += "<strong>Interval:</strong> Not specified</p>\n"

        report += "<h2>Summary Statistics</h2>\n"
        report += "<table>\n"
        report += "<tr><th>Topic</th><th>Average Sentiment</th><th>Total Articles</th></tr>\n"
        for topic, stats in topic_stats.items():
            report += f"<tr><td>{topic}</td><td>{stats['avg_sentiment']:.2f}</td><td>{stats['total_articles']}</td></tr>\n"
        report += "</table>\n"

        report += "<h2>Detailed Comparison</h2>\n"

        # Get all unique periods across all topics
        all_periods = set()
        for topic_data in data.values():
            all_periods.update(topic_data.time_periods)

        # Sort periods
        sorted_periods = sorted(all_periods)

        # Create table
        report += "<table>\n<tr><th>Period</th>"
        for topic in data.keys():
            report += f"<th>{topic}</th>"
        report += "</tr>\n"

        # Add data rows
        for period in sorted_periods:
            report += f"<tr><td>{period}</td>"
            for topic, topic_data in data.items():
                try:
                    idx = topic_data.time_periods.index(period)
                    sentiment = topic_data.sentiment_values[idx]
                    report += f"<td>{sentiment:.2f}</td>"
                except ValueError:
                    report += "<td>N/A</td>"
            report += "</tr>\n"

        report += "</table>\n"
        report += "</body></html>"
        return report
