#!/usr/bin/env python3
"""
Script to demonstrate sentiment analysis functionality.

This script shows how to use the sentiment analysis feature by:
1. Analyzing sentiment for existing articles
2. Tracking sentiment trends over time
3. Detecting shifts in public opinion
4. Generating sentiment reports in various formats
"""

import argparse
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy.orm import Session

from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
from local_newsifier.crud.article import article as article_crud
from local_newsifier.database.engine import get_session
from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.article import Article
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from local_newsifier.tools.sentiment_tracker import SentimentTracker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def add_sample_articles(session: Session):
    """Add sample articles to the database."""
    logger.info("Adding sample articles...")

    # Get current timestamp for unique URLs
    timestamp = int(datetime.now(timezone.utc).timestamp())

    # Sample articles with different sentiment profiles
    articles = [
        {
            "url": f"https://example.com/business-success-{timestamp}",
            "title": "Local Business Thrives After Community Support",
            "source": "Local News",
            "content": (
                "The new downtown cafe has seen remarkable success since opening "
                "last month. Owner Sarah Johnson credits the warm welcome from "
                "local residents. 'The community has been incredibly supportive,' "
                "she said. Several customers praised the cafe's atmosphere and "
                "quality service."
            ),
            "published_at": datetime.now(timezone.utc),
            "status": "new",
            "scraped_at": datetime.now(timezone.utc),
        },
        {
            "url": f"https://example.com/development-controversy-{timestamp}",
            "title": "Controversial Development Project Faces Opposition",
            "source": "Local News",
            "content": (
                "Strong concerns were raised about the proposed high-rise "
                "development at last night's city council meeting. Residents "
                "cited potential traffic issues and impact on neighborhood "
                "character. 'Our community deserves better,' said long-time "
                "resident Michael Brown. The developer's representative faced "
                "persistent criticism throughout the session."
            ),
            "published_at": datetime.now(timezone.utc),
            "status": "new",
            "scraped_at": datetime.now(timezone.utc),
        },
        {
            "url": f"https://example.com/city-policy-{timestamp}",
            "title": "Mixed Reactions to New City Policy",
            "source": "Local News",
            "content": (
                "The city's new parking policy has drawn both praise and "
                "criticism from business owners. While some welcome the extended "
                "hours, others worry about increased congestion. Council member "
                "Jane Smith defended the policy as 'a step in the right "
                "direction,' despite mixed public opinion."
            ),
            "published_at": datetime.now(timezone.utc),
            "status": "new",
            "scraped_at": datetime.now(timezone.utc),
        },
    ]

    for article_data in articles:
        try:
            article = Article(**article_data)
            created_article = article_crud.create(session, obj_in=article)
            logger.info(f"Added article: {created_article.title}")
        except Exception as e:
            logger.error(f"Error adding article: {e}")


def analyze_articles(session: Session, article_ids: List[int]):
    """Analyze sentiment for articles."""
    sentiment_analyzer = SentimentAnalysisTool()

    for article_id in article_ids:
        article = article_crud.get(session, id=article_id)
        if not article:
            continue

        logger.info(f"\nArticle {article.id}: {article.title}")

        # Create analysis state
        state = NewsAnalysisState(
            target_url=article.url,
            scraped_text=article.content,
            status=AnalysisStatus.INITIALIZED,
            analysis_results={},
        )

        # Analyze sentiment
        state = sentiment_analyzer.analyze_sentiment(state)

        if state.analysis_results and "sentiment" in state.analysis_results:
            sentiment_data = state.analysis_results["sentiment"]

            # Store analysis results
            analysis_result = AnalysisResult(
                article_id=article.id,
                analysis_type="sentiment",
                results={
                    "document_sentiment": sentiment_data["document_sentiment"],
                    "document_magnitude": sentiment_data["document_magnitude"],
                    "topic_sentiments": sentiment_data["topic_sentiments"],
                },
            )
            analysis_result_crud.create(session, obj_in=analysis_result)

            # Log results
            logger.info(f"Document Sentiment: {sentiment_data['document_sentiment']}")
            logger.info(f"Document Magnitude: {sentiment_data['document_magnitude']}")
            logger.info("\nTopic Sentiments:")
            for topic, sentiment in sentiment_data["topic_sentiments"].items():
                logger.info(f"  {topic}: {sentiment}")

            # Update article status
            article_crud.update_status(session, article_id=article.id, status="analyzed")
        else:
            logger.warning("No sentiment analysis results available")


def analyze_trends(session: Session):
    """Analyze sentiment trends."""
    sentiment_tracker = SentimentTracker(session=session)

    # Analyze trends for the past week
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)

    logger.info(f"Analyzing trends from {start_date} to {end_date}")

    # Get sentiment trends
    trends = sentiment_tracker.get_sentiment_by_period(
        start_date=start_date, end_date=end_date, time_interval="day"
    )

    # Display results
    for period, data in trends.items():
        logger.info(f"\nPeriod: {period}")
        if "overall" in data:
            logger.info(f"Average Sentiment: {data['overall']['avg_sentiment']}")
            logger.info(f"Article Count: {data['overall']['article_count']}")
            logger.info("\nSentiment Distribution:")
            distribution = data["overall"]["sentiment_distribution"]
            for sentiment, count in distribution.items():
                logger.info(f"  {sentiment.title()}: {count}")


def show_topic_trends(flow, topics, days=30, interval="day"):
    """
    Show sentiment trends for specific topics.

    Args:
        flow: PublicOpinionFlow instance
        topics: List of topics to analyze
        days: Number of days to look back
        interval: Time interval for grouping
    """
    logger.info(f"Analyzing sentiment trends for topics: {', '.join(topics)}")

    # Analyze topic sentiment
    results = flow.analyze_topic_sentiment(topics=topics, days_back=days, interval=interval)

    # Display results
    logger.info(
        f"Time period: {results['date_range']['start']} to " f"{results['date_range']['end']}"
    )

    # Display sentiment by period
    logger.info("Sentiment by period:")
    for period, data in sorted(results["sentiment_by_period"].items()):
        logger.info(f"  {period}:")
        for topic, topic_data in data.items():
            if topic != "overall":
                logger.info(
                    f"    {topic}: {topic_data.get('avg_sentiment', 0):.2f} "
                    f"({topic_data.get('article_count', 0)} articles)"
                )

    # Display significant shifts
    if results["sentiment_shifts"]:
        logger.info("Significant sentiment shifts detected:")
        for shift in results["sentiment_shifts"]:
            logger.info(
                f"  {shift['topic']}: {shift['start_period']} to {shift['end_period']}, "
                f"change: {shift['shift_magnitude']:.2f}"
            )
    else:
        logger.info("No significant sentiment shifts detected")


def compare_topics(flow, topic_pairs, days=30, interval="day"):
    """
    Compare sentiment between pairs of topics.

    Args:
        flow: PublicOpinionFlow instance
        topic_pairs: List of topic pairs to compare
        days: Number of days to look back
        interval: Time interval for grouping
    """
    logger.info("Comparing topic sentiments...")

    # Calculate correlations
    correlations = flow.correlate_topics(topic_pairs=topic_pairs, days_back=days, interval=interval)

    # Display results
    for correlation in correlations:
        topic1 = correlation["topic1"]
        topic2 = correlation["topic2"]
        corr_value = correlation["correlation"]

        relationship = (
            "strong positive correlation"
            if corr_value > 0.7
            else (
                "moderate positive correlation"
                if corr_value > 0.3
                else (
                    "weak positive correlation"
                    if corr_value > 0
                    else (
                        "strong negative correlation"
                        if corr_value < -0.7
                        else (
                            "moderate negative correlation"
                            if corr_value < -0.3
                            else "weak negative correlation"
                        )
                    )
                )
            )
        )

        logger.info(f"{topic1} and {topic2}: {corr_value:.2f} ({relationship})")


def generate_report(flow, topic, days=30, format_type="markdown", output_file=None):
    """
    Generate a sentiment analysis report for a topic.

    Args:
        flow: PublicOpinionFlow instance
        topic: Topic to analyze
        days: Number of days to look back
        format_type: Report format
        output_file: Optional file to save report
    """
    logger.info(f"Generating {format_type} report for topic: {topic}")

    # Generate report
    report = flow.generate_topic_report(topic=topic, days_back=days, format_type=format_type)

    # Save or display report
    if output_file:
        with open(output_file, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {output_file}")
    else:
        print("\n" + "=" * 80)
        print(report)
        print("=" * 80)


def generate_comparison_report(flow, topics, days=30, format_type="markdown", output_file=None):
    """
    Generate a comparison report for multiple topics.

    Args:
        flow: PublicOpinionFlow instance
        topics: List of topics to compare
        days: Number of days to look back
        format_type: Report format
        output_file: Optional file to save report
    """
    logger.info(f"Generating {format_type} comparison report for topics: {', '.join(topics)}")

    # Generate report
    report = flow.generate_comparison_report(topics=topics, days_back=days, format_type=format_type)

    # Save or display report
    if output_file:
        with open(output_file, "w") as f:
            f.write(report)
        logger.info(f"Comparison report saved to {output_file}")
    else:
        print("\n" + "=" * 80)
        print(report)
        print("=" * 80)


def generate_html_report(results: Dict, output_file: str = "sentiment_report.html"):
    """Generate a simple HTML report of sentiment analysis results."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sentiment Analysis Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1, h2 { color: #333; }
            .article { margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }
            .positive { color: green; }
            .negative { color: red; }
            .neutral { color: gray; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Sentiment Analysis Report</h1>
    """

    # Add article analysis results
    html += "<h2>Article Analysis</h2>"
    for article_id, result in results["article_analysis"].items():
        sentiment_class = (
            "positive"
            if result["document_sentiment"] > 0.1
            else "negative" if result["document_sentiment"] < -0.1 else "neutral"
        )
        html += f"""
        <div class="article">
            <h3>Article {article_id}</h3>
            <p>Document Sentiment: <span class="{sentiment_class}">"""
        html += f"{result['document_sentiment']:.2f}</span></p>"
        html += f"""
            <p>Document Magnitude: {result['document_magnitude']:.2f}</p>

            <h4>Entity Sentiments</h4>
            <table>
                <tr><th>Entity</th><th>Sentiment</th></tr>
        """
        for entity, sentiment in result["entity_sentiments"].items():
            sentiment_class = (
                "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"
            )
            html += (
                f"<tr><td>{entity}</td>" f"<td class='{sentiment_class}'>{sentiment:.2f}</td></tr>"
            )
        html += """
            </table>

            <h4>Topic Sentiments</h4>
            <table>
                <tr><th>Topic</th><th>Sentiment</th></tr>
        """
        for topic, sentiment in result["topic_sentiments"].items():
            sentiment_class = (
                "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"
            )
            html += (
                f"<tr><td>{topic}</td>" f"<td class='{sentiment_class}'>{sentiment:.2f}</td></tr>"
            )
        html += """
            </table>
        </div>
        """

    # Add trend analysis results
    html += "<h2>Trend Analysis</h2>"
    for period, data in results["trend_analysis"].items():
        html += f"""
        <div class="period">
            <h3>Period: {period}</h3>
            <p>Average Sentiment: {data['overall']['avg_sentiment']:.2f}</p>
            <p>Article Count: {data['overall']['article_count']}</p>

            <h4>Sentiment Distribution</h4>
            <table>
                <tr><th>Category</th><th>Count</th></tr>
"""
        positive_count = data["overall"]["sentiment_distribution"]["positive"]
        neutral_count = data["overall"]["sentiment_distribution"]["neutral"]
        negative_count = data["overall"]["sentiment_distribution"]["negative"]
        html += f"""
                <tr><td>Positive</td><td>{positive_count}</td></tr>
                <tr><td>Neutral</td><td>{neutral_count}</td></tr>
                <tr><td>Negative</td><td>{negative_count}</td></tr>
            </table>
        </div>
        """

    html += """
    </body>
    </html>
    """

    with open(output_file, "w") as f:
        f.write(html)
    logger.info(f"Generated HTML report: {output_file}")


def main():
    """Run the sentiment analysis demo."""
    parser = argparse.ArgumentParser(description="Sentiment analysis demo script")
    parser.add_argument("--days", type=int, default=30, help="Number of days to analyze")
    parser.add_argument("--topics", nargs="+", help="Topics to analyze")
    args = parser.parse_args()

    # Use a context manager for the session
    with get_session() as session:
        # Add sample articles
        add_sample_articles(session)

        # Get all articles and their IDs
        articles = session.query(Article).all()
        # Explicitly convert to int
        article_ids = [int(article.id) for article in articles]

        # Analyze articles
        analyze_articles(session, article_ids)

        # Analyze trends
        analyze_trends(session)

        # Initialize public opinion flow
        flow = PublicOpinionFlow(session=session)

        # Show topic trends if topics are provided
        if args.topics:
            show_topic_trends(flow, args.topics, days=args.days)

            # Compare pairs of topics if multiple topics provided
            if len(args.topics) > 1:
                topic_pairs = [
                    (args.topics[i], args.topics[i + 1]) for i in range(len(args.topics) - 1)
                ]
                compare_topics(flow, topic_pairs, days=args.days)


if __name__ == "__main__":
    main()
