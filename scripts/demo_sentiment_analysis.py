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
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from local_newsifier.config.database import get_db_session
from local_newsifier.database.manager import DatabaseManager
from local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
from local_newsifier.models.database.article import ArticleCreate, ArticleDB
from local_newsifier.models.database.analysis_result import AnalysisResultCreate
from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from local_newsifier.tools.sentiment_tracker import SentimentTracker
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def add_sample_articles(db_manager: DatabaseManager):
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
                "The new downtown cafe has seen remarkable success since opening last month. "
                "Owner Sarah Johnson credits the warm welcome from local residents. "
                "'The community has been incredibly supportive,' she said. "
                "Several customers praised the cafe's atmosphere and quality service."
            ),
            "published_at": datetime.now(timezone.utc),
            "status": "new"
        },
        {
            "url": f"https://example.com/development-controversy-{timestamp}",
            "title": "Controversial Development Project Faces Opposition",
            "source": "Local News",
            "content": (
                "Strong concerns were raised about the proposed high-rise development at "
                "last night's city council meeting. Residents cited potential traffic issues "
                "and impact on neighborhood character. 'Our community deserves better,' said "
                "long-time resident Michael Brown. The developer's representative faced "
                "persistent criticism throughout the session."
            ),
            "published_at": datetime.now(timezone.utc),
            "status": "new"
        },
        {
            "url": f"https://example.com/city-policy-{timestamp}",
            "title": "Mixed Reactions to New City Policy",
            "source": "Local News",
            "content": (
                "The city's new parking policy has drawn both praise and criticism from "
                "business owners. While some welcome the extended hours, others worry about "
                "increased congestion. Council member Jane Smith defended the policy as "
                "'a step in the right direction,' despite mixed public opinion."
            ),
            "published_at": datetime.now(timezone.utc),
            "status": "new"
        }
    ]

    for article_data in articles:
        try:
            article = ArticleCreate(**article_data)
            created_article = db_manager.create_article(article)
            logger.info(f"Added article: {created_article.title}")
        except Exception as e:
            logger.error(f"Error adding article: {e}")


def analyze_articles(db_manager: DatabaseManager, article_ids: List[int]):
    """Analyze sentiment for articles."""
    sentiment_analyzer = SentimentAnalysisTool()
    
    for article_id in article_ids:
        article = db_manager.get_article(article_id)
        if not article:
            continue
            
        logger.info(f"\nArticle {article.id}: {article.title}")
        
        # Create analysis state
        state = NewsAnalysisState(
            target_url=article.url,
            scraped_text=article.content,
            status=AnalysisStatus.INITIALIZED,
            analysis_results={}
        )
        
        # Analyze sentiment
        state = sentiment_analyzer.analyze(state)
        
        if state.analysis_results and "sentiment" in state.analysis_results:
            sentiment_data = state.analysis_results["sentiment"]
            
            # Store analysis results
            analysis_result = AnalysisResultCreate(
                article_id=article.id,
                analysis_type="sentiment",
                results={
                    "document_sentiment": sentiment_data["document_sentiment"],
                    "document_magnitude": sentiment_data["document_magnitude"],
                    "topic_sentiments": sentiment_data["topic_sentiments"]
                }
            )
            db_manager.add_analysis_result(analysis_result)
            
            # Log results
            logger.info(f"Document Sentiment: {sentiment_data['document_sentiment']}")
            logger.info(f"Document Magnitude: {sentiment_data['document_magnitude']}")
            logger.info("\nTopic Sentiments:")
            for topic, sentiment in sentiment_data["topic_sentiments"].items():
                logger.info(f"  {topic}: {sentiment}")
                
            # Update article status
            db_manager.update_article_status(article.id, "analyzed")
        else:
            logger.warning("No sentiment analysis results available")


def analyze_trends(db_manager: DatabaseManager):
    """Analyze sentiment trends."""
    sentiment_tracker = SentimentTracker(db_manager)
    
    # Analyze trends for the past week
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)
    
    logger.info(f"Analyzing trends from {start_date} to {end_date}")
    
    # Get sentiment trends
    trends = sentiment_tracker.get_sentiment_by_period(
        start_date=start_date,
        end_date=end_date,
        time_interval="day"
    )
    
    # Display results
    for period, data in trends.items():
        logger.info(f"\nPeriod: {period}")
        if "overall" in data:
            logger.info(f"Average Sentiment: {data['overall']['avg_sentiment']}")
            logger.info(f"Article Count: {data['overall']['article_count']}")
            logger.info("\nSentiment Distribution:")
            for sentiment, count in data["overall"]["sentiment_distribution"].items():
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
    results = flow.analyze_topic_sentiment(
        topics=topics,
        days_back=days,
        interval=interval
    )
    
    # Display results
    logger.info(f"Time period: {results['date_range']['start']} to {results['date_range']['end']}")
    
    # Display sentiment by period
    logger.info("Sentiment by period:")
    for period, data in sorted(results["sentiment_by_period"].items()):
        logger.info(f"  {period}:")
        for topic, topic_data in data.items():
            if topic != "overall":
                logger.info(f"    {topic}: {topic_data.get('avg_sentiment', 0):.2f} "
                          f"({topic_data.get('article_count', 0)} articles)")
    
    # Display significant shifts
    if results["sentiment_shifts"]:
        logger.info("Significant sentiment shifts detected:")
        for shift in results["sentiment_shifts"]:
            logger.info(f"  {shift['topic']}: {shift['start_period']} to {shift['end_period']}, "
                      f"change: {shift['shift_magnitude']:.2f}")
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
    correlations = flow.correlate_topics(
        topic_pairs=topic_pairs,
        days_back=days,
        interval=interval
    )
    
    # Display results
    for correlation in correlations:
        topic1 = correlation["topic1"]
        topic2 = correlation["topic2"]
        corr_value = correlation["correlation"]
        
        relationship = "strong positive correlation" if corr_value > 0.7 else \
                       "moderate positive correlation" if corr_value > 0.3 else \
                       "weak positive correlation" if corr_value > 0 else \
                       "strong negative correlation" if corr_value < -0.7 else \
                       "moderate negative correlation" if corr_value < -0.3 else \
                       "weak negative correlation"
        
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
    report = flow.generate_topic_report(
        topic=topic,
        days_back=days,
        format_type=format_type
    )
    
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
    report = flow.generate_comparison_report(
        topics=topics,
        days_back=days,
        format_type=format_type
    )
    
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
        sentiment_class = "positive" if result["document_sentiment"] > 0.1 else "negative" if result["document_sentiment"] < -0.1 else "neutral"
        html += f"""
        <div class="article">
            <h3>Article {article_id}</h3>
            <p>Document Sentiment: <span class="{sentiment_class}">{result['document_sentiment']:.2f}</span></p>
            <p>Document Magnitude: {result['document_magnitude']:.2f}</p>
            
            <h4>Entity Sentiments</h4>
            <table>
                <tr><th>Entity</th><th>Sentiment</th></tr>
        """
        for entity, sentiment in result["entity_sentiments"].items():
            sentiment_class = "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"
            html += f"<tr><td>{entity}</td><td class='{sentiment_class}'>{sentiment:.2f}</td></tr>"
        html += """
            </table>
            
            <h4>Topic Sentiments</h4>
            <table>
                <tr><th>Topic</th><th>Sentiment</th></tr>
        """
        for topic, sentiment in result["topic_sentiments"].items():
            sentiment_class = "positive" if sentiment > 0.1 else "negative" if sentiment < -0.1 else "neutral"
            html += f"<tr><td>{topic}</td><td class='{sentiment_class}'>{sentiment:.2f}</td></tr>"
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
                <tr><td>Positive</td><td>{data['overall']['sentiment_distribution']['positive']}</td></tr>
                <tr><td>Neutral</td><td>{data['overall']['sentiment_distribution']['neutral']}</td></tr>
                <tr><td>Negative</td><td>{data['overall']['sentiment_distribution']['negative']}</td></tr>
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

    # Initialize database connection
    session_factory = get_db_session()
    session = session_factory()
    db_manager = DatabaseManager(session)

    try:
        # Add sample articles
        add_sample_articles(db_manager)

        # Get all articles and their IDs
        articles = db_manager.session.query(ArticleDB).all()
        article_ids = [int(article.id) for article in articles]  # Explicitly convert to int

        # Analyze articles
        analyze_articles(db_manager, article_ids)

        # Analyze trends
        analyze_trends(db_manager)

        # Initialize public opinion flow
        flow = PublicOpinionFlow(db_manager)

        # Show topic trends if topics are provided
        if args.topics:
            show_topic_trends(flow, args.topics, days=args.days)

            # Compare pairs of topics if multiple topics provided
            if len(args.topics) > 1:
                topic_pairs = [(args.topics[i], args.topics[i+1]) 
                             for i in range(len(args.topics)-1)]
                compare_topics(flow, topic_pairs, days=args.days)

    finally:
        session.close()


if __name__ == "__main__":
    main()