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

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.local_newsifier.config.database import get_database_settings
from src.local_newsifier.database.manager import DatabaseManager
from src.local_newsifier.flows.public_opinion_flow import PublicOpinionFlow
from src.local_newsifier.models.database import get_session, init_db

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def analyze_articles(flow, count=None):
    """
    Analyze sentiment for unanalyzed articles.
    
    Args:
        flow: PublicOpinionFlow instance
        count: Optional max number of articles to analyze
    """
    logger.info("Starting sentiment analysis for articles...")
    
    # Get articles that need sentiment analysis
    articles = flow.db_manager.get_articles_by_status("analyzed")
    if count:
        articles = articles[:count]
    
    article_ids = [article.id for article in articles]
    
    if not article_ids:
        logger.info("No articles found to analyze")
        return
    
    logger.info(f"Analyzing sentiment for {len(article_ids)} articles...")
    
    # Analyze articles
    results = flow.analyze_articles(article_ids)
    
    # Display summary
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for article_id, result in results.items():
        if "error" in result:
            logger.error(f"Error analyzing article {article_id}: {result['error']}")
            continue
            
        sentiment = result["document_sentiment"]
        if sentiment > 0.1:
            positive_count += 1
        elif sentiment < -0.1:
            negative_count += 1
        else:
            neutral_count += 1
    
    logger.info(f"Analysis complete: {positive_count} positive, {negative_count} negative, {neutral_count} neutral")


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


def main():
    """Main function to run the demonstration script."""
    parser = argparse.ArgumentParser(description="Sentiment Analysis Demonstration")
    parser.add_argument("--mode", choices=["analyze", "trends", "compare", "report"], 
                        default="analyze", help="Demonstration mode")
    parser.add_argument("--topics", nargs="+", help="Topics to analyze")
    parser.add_argument("--topic-pairs", nargs="+", help="Topic pairs to compare (topic1:topic2)")
    parser.add_argument("--days", type=int, default=30, help="Number of days to look back")
    parser.add_argument("--interval", choices=["day", "week", "month"], 
                        default="day", help="Time interval for grouping")
    parser.add_argument("--format", choices=["text", "markdown", "html"], 
                        default="markdown", help="Report format")
    parser.add_argument("--output", help="Output file for reports")
    parser.add_argument("--count", type=int, help="Maximum number of articles to analyze")
    
    args = parser.parse_args()
    
    # Initialize database
    db_settings = get_database_settings()
    engine = init_db(str(db_settings.DATABASE_URL))
    session_factory = get_session(engine)
    session = session_factory()
    db_manager = DatabaseManager(session)
    
    # Create flow
    flow = PublicOpinionFlow(db_manager=db_manager)
    
    try:
        if args.mode == "analyze":
            analyze_articles(flow, args.count)
            
        elif args.mode == "trends":
            if not args.topics:
                logger.error("No topics specified. Use --topics to specify topics.")
                return
            show_topic_trends(flow, args.topics, args.days, args.interval)
            
        elif args.mode == "compare":
            if not args.topic_pairs:
                logger.error("No topic pairs specified. Use --topic-pairs to specify pairs (topic1:topic2).")
                return
                
            # Parse topic pairs
            pairs = []
            for pair in args.topic_pairs:
                if ":" in pair:
                    topic1, topic2 = pair.split(":", 1)
                    pairs.append((topic1, topic2))
                else:
                    logger.warning(f"Invalid topic pair format: {pair}. Should be topic1:topic2")
            
            if pairs:
                compare_topics(flow, pairs, args.days, args.interval)
            
        elif args.mode == "report":
            if not args.topics:
                logger.error("No topics specified. Use --topics to specify topics.")
                return
                
            if len(args.topics) == 1:
                # Single topic report
                generate_report(flow, args.topics[0], args.days, args.format, args.output)
            else:
                # Comparison report
                generate_comparison_report(flow, args.topics, args.days, args.format, args.output)
                
    finally:
        # Clean up
        session.close()


if __name__ == "__main__":
    main()