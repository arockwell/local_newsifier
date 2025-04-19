#!/usr/bin/env python
"""Demo script to showcase the refactored sentiment analysis architecture."""

from datetime import datetime, timedelta, timezone
from pprint import pprint

from local_newsifier.core.factory import ToolFactory, ServiceFactory
from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.flows.sentiment_analysis_flow_v2 import SentimentAnalysisFlow


def main():
    """Run the demo script."""
    print("Demonstrating refactored sentiment analysis architecture...")
    
    # Get the session manager
    session_manager = get_session_manager()
    
    # Create services using factories
    sentiment_service = ServiceFactory.create_sentiment_service(
        session_manager=session_manager
    )
    
    # Create tools using factories
    sentiment_analyzer = ToolFactory.create_sentiment_analyzer(
        session_manager=session_manager,
        sentiment_service=sentiment_service
    )
    
    # Create flows using the tools
    sentiment_flow = SentimentAnalysisFlow(
        session_manager=session_manager,
        sentiment_analyzer=sentiment_analyzer
    )
    
    # Process any new articles
    print("\nAnalyzing new articles...")
    try:
        results = sentiment_flow.analyze_new_articles()
        print(f"Analyzed {len(results)} articles.")
        if results:
            print("\nSample article results:")
            pprint(results[0])
    except Exception as e:
        print(f"Error analyzing articles: {e}")
    
    # Get sentiment trends
    print("\nGenerating sentiment trends (last 30 days)...")
    try:
        trends = sentiment_flow.get_sentiment_trends(days=30)
        print("\nSentiment trends by day:")
        for date, data in trends["daily_averages"].items():
            print(f"- {date}: {data['average']:.2f} (from {data['count']} articles)")
            
        print("\nTop entity sentiments:")
        for entity, data in list(trends["entity_sentiment"].items())[:5]:
            avg_sentiment = sum(item["sentiment"] for item in data) / len(data) if data else 0
            print(f"- {entity}: {avg_sentiment:.2f} (from {len(data)} mentions)")
    except Exception as e:
        print(f"Error generating trends: {e}")
    
    # Show entity sentiment dashboard
    print("\nDemonstrating entity sentiment dashboard for 'Joe Biden':")
    try:
        dashboard = sentiment_flow.get_entity_sentiment_dashboard("Joe Biden", days=30)
        print(f"Found {dashboard['mention_count']} mentions with average sentiment: {dashboard['average_sentiment']:.2f}")
        print("\nSentiment breakdown:")
        print(f"- Positive: {dashboard['sentiment_breakdown']['positive']}")
        print(f"- Neutral: {dashboard['sentiment_breakdown']['neutral']}")
        print(f"- Negative: {dashboard['sentiment_breakdown']['negative']}")
        
        if dashboard["recent_mentions"]:
            print("\nMost recent mentions:")
            for mention in dashboard["recent_mentions"][:3]:
                print(f"- Article: {mention['article_title']}")
                print(f"  Sentiment: {mention['sentiment_score']:.2f}")
                print(f"  Date: {mention['date'].strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error generating dashboard: {e}")
    
    # Using the service directly
    print("\nDemonstrating direct service usage:")
    try:
        # Get article sentiment
        article_id = 1  # Assuming article ID 1 exists
        sentiment = sentiment_service.get_article_sentiment(article_id)
        if sentiment:
            print(f"Article sentiment: {sentiment['document_sentiment']:.2f}")
        else:
            print("No sentiment data found for this article")
    except Exception as e:
        print(f"Error getting article sentiment: {e}")
    
    print("\nRefactored sentiment analysis demo complete.")


if __name__ == "__main__":
    main()
