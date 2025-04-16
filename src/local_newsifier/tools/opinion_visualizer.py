"""Tool for visualizing sentiment and opinion data."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union

from sqlmodel import Session, select

from ..database.engine import with_session
from ..models.sentiment import SentimentVisualizationData

logger = logging.getLogger(__name__)


class OpinionVisualizerTool:
    """Tool for generating visualizations of sentiment and opinion data."""

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize the opinion visualizer.

        Args:
            session: Optional SQLModel session
        """
        self.session = session

    @with_session
    def prepare_timeline_data(
        self,
        topic: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
        *,
        session: Optional[Session] = None
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
        # Use provided session or instance session
        session = session or self.session

        # Import necessary classes here to avoid circular imports
        from ..models.database.analysis_result import AnalysisResult
        from ..models.database.article import Article
        
        # Get analysis results for the topic using SQLModel syntax
        statement = select(AnalysisResult).where(
            AnalysisResult.analysis_type == "SENTIMENT",
            Article.published_at >= start_date,
            Article.published_at <= end_date
        ).join(Article)
        
        results = session.exec(statement)
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
                sentiments = [
                    r.results["topic_sentiments"][topic] for r in period_results
                ]
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
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "interval": interval,
            },
        )

    @with_session
    def prepare_comparison_data(
        self,
        topics: List[str],
        start_date: datetime,
        end_date: datetime,
        interval: str = "day",
        *,
        session: Optional[Session] = None
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
        # Use provided session or instance session
        session = session or self.session
        
        comparison_data = {}

        for topic in topics:
            topic_data = self.prepare_timeline_data(
                topic, start_date, end_date, interval, session=session
            )
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
        if report_type == "timeline" and isinstance(
            visualization_data, SentimentVisualizationData
        ):
            return self._generate_timeline_text_report(visualization_data)
        elif report_type == "comparison" and isinstance(visualization_data, dict):
            return self._generate_comparison_text_report(visualization_data)
        else:
            raise ValueError(
                f"Invalid report type: {report_type} or data type mismatch"
            )

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
        if report_type == "timeline" and isinstance(
            visualization_data, SentimentVisualizationData
        ):
            return self._generate_timeline_markdown_report(visualization_data)
        elif report_type == "comparison" and isinstance(visualization_data, dict):
            return self._generate_comparison_markdown_report(visualization_data)
        else:
            raise ValueError(
                f"Invalid report type: {report_type} or data type mismatch"
            )

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
        if report_type == "timeline" and isinstance(
            visualization_data, SentimentVisualizationData
        ):
            return self._generate_timeline_html_report(visualization_data)
        elif report_type == "comparison" and isinstance(visualization_data, dict):
            return self._generate_comparison_html_report(visualization_data)
        else:
            raise ValueError(
                f"Invalid report type: {report_type} or data type mismatch"
            )

    def _generate_timeline_text_report(self, data: SentimentVisualizationData) -> str:
        """Generate a text report for timeline visualization."""
        # Calculate summary statistics
        if not data.sentiment_values:
            return f"No sentiment data available for topic: {data.topic}"

        avg_sentiment = sum(data.sentiment_values) / len(data.sentiment_values)
        min_sentiment = min(data.sentiment_values)
        max_sentiment = max(data.sentiment_values)
        total_articles = sum(data.article_counts)

        # Build report
        report = f"SENTIMENT ANALYSIS REPORT: {data.topic}\n"
        report += "=" * 50 + "\n\n"

        report += f"Time period: {data.metadata['start_date']} to {data.metadata['end_date']}\n"
        report += f"Interval: {data.metadata['interval']}\n\n"

        report += "SUMMARY STATISTICS\n"
        report += f"Average sentiment: {avg_sentiment:.2f}\n"
        report += f"Minimum sentiment: {min_sentiment:.2f}\n"
        report += f"Maximum sentiment: {max_sentiment:.2f}\n"
        report += f"Total articles: {total_articles}\n\n"

        report += "SENTIMENT TIMELINE\n"
        for i, period in enumerate(data.time_periods):
            sentiment = data.sentiment_values[i]
            articles = data.article_counts[i]
            report += f"{period}: {sentiment:.2f} ({articles} articles)\n"

        return report

    def _generate_comparison_text_report(
        self, data: Dict[str, SentimentVisualizationData]
    ) -> str:
        """Generate a text report for comparison visualization."""
        if not data:
            return "No sentiment data available for comparison"

        # Get metadata from first entry
        first_topic = list(data.keys())[0]
        metadata = data[first_topic].metadata

        # Build report
        report = "SENTIMENT COMPARISON REPORT\n"
        report += "=" * 50 + "\n\n"

        report += f"Time period: {metadata['start_date']} to {metadata['end_date']}\n"
        report += f"Interval: {metadata['interval']}\n\n"

        report += "SUMMARY STATISTICS\n"
        for topic, topic_data in data.items():
            if not topic_data.sentiment_values:
                continue

            avg_sentiment = sum(topic_data.sentiment_values) / len(
                topic_data.sentiment_values
            )
            total_articles = sum(topic_data.article_counts)
            report += f"{topic}: {avg_sentiment:.2f} ({total_articles} articles)\n"

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

    def _generate_timeline_markdown_report(
        self, data: SentimentVisualizationData
    ) -> str:
        """Generate a markdown report for timeline visualization."""
        # Calculate summary statistics
        if not data.sentiment_values:
            return f"No sentiment data available for topic: {data.topic}"

        avg_sentiment = sum(data.sentiment_values) / len(data.sentiment_values)
        min_sentiment = min(data.sentiment_values)
        max_sentiment = max(data.sentiment_values)
        total_articles = sum(data.article_counts)

        # Build report
        report = f"# Sentiment Analysis Report: {data.topic}\n\n"

        report += f"**Time period:** {data.metadata['start_date']} to {data.metadata['end_date']}  \n"
        report += f"**Interval:** {data.metadata['interval']}\n\n"

        report += "## Summary Statistics\n\n"
        report += f"- **Average sentiment:** {avg_sentiment:.2f}\n"
        report += f"- **Minimum sentiment:** {min_sentiment:.2f}\n"
        report += f"- **Maximum sentiment:** {max_sentiment:.2f}\n"
        report += f"- **Total articles:** {total_articles}\n\n"

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

        # Get metadata from first entry
        first_topic = list(data.keys())[0]
        metadata = data[first_topic].metadata

        # Build report
        report = "# Sentiment Comparison Report\n\n"

        report += (
            f"**Time period:** {metadata['start_date']} to {metadata['end_date']}  \n"
        )
        report += f"**Interval:** {metadata['interval']}\n\n"

        report += "## Summary Statistics\n\n"
        report += "| Topic | Average Sentiment | Total Articles |\n"
        report += "|-------|------------------|----------------|\n"
        for topic, topic_data in data.items():
            if not topic_data.sentiment_values:
                continue

            avg_sentiment = sum(topic_data.sentiment_values) / len(
                topic_data.sentiment_values
            )
            total_articles = sum(topic_data.article_counts)
            report += f"| {topic} | {avg_sentiment:.2f} | {total_articles} |\n"

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

        avg_sentiment = sum(data.sentiment_values) / len(data.sentiment_values)
        min_sentiment = min(data.sentiment_values)
        max_sentiment = max(data.sentiment_values)
        total_articles = sum(data.article_counts)

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

        report += f"<p><strong>Time period:</strong> {data.metadata['start_date']} to {data.metadata['end_date']}<br>\n"
        report += f"<strong>Interval:</strong> {data.metadata['interval']}</p>\n"

        report += "<h2>Summary Statistics</h2>\n"
        report += "<ul>\n"
        report += f"<li><strong>Average sentiment:</strong> {avg_sentiment:.2f}</li>\n"
        report += f"<li><strong>Minimum sentiment:</strong> {min_sentiment:.2f}</li>\n"
        report += f"<li><strong>Maximum sentiment:</strong> {max_sentiment:.2f}</li>\n"
        report += f"<li><strong>Total articles:</strong> {total_articles}</li>\n"
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

    def _generate_comparison_html_report(
        self, data: Dict[str, SentimentVisualizationData]
    ) -> str:
        """Generate an HTML report for comparison visualization."""
        if not data:
            return "<p>No sentiment data available for comparison</p>"

        # Get metadata from first entry
        first_topic = list(data.keys())[0]
        metadata = data[first_topic].metadata

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

        report += f"<p><strong>Time period:</strong> {metadata['start_date']} to {metadata['end_date']}<br>\n"
        report += f"<strong>Interval:</strong> {metadata['interval']}</p>\n"

        report += "<h2>Summary Statistics</h2>\n"
        report += "<table>\n"
        report += (
            "<tr><th>Topic</th><th>Average Sentiment</th><th>Total Articles</th></tr>\n"
        )
        for topic, topic_data in data.items():
            if not topic_data.sentiment_values:
                continue

            avg_sentiment = sum(topic_data.sentiment_values) / len(
                topic_data.sentiment_values
            )
            total_articles = sum(topic_data.article_counts)
            report += f"<tr><td>{topic}</td><td>{avg_sentiment:.2f}</td><td>{total_articles}</td></tr>\n"
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
