"""Demo script for sentiment analysis and public opinion tracking."""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from src.local_newsifier.config.database import get_database_settings
from src.local_newsifier.database.manager import DatabaseManager
from src.local_newsifier.models.database import init_db, get_session
from src.local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from src.local_newsifier.tools.sentiment_tracker import SentimentTracker
from src.local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool


async def analyze_sample_articles():
    """Analyze sample articles and demonstrate sentiment analysis features."""
    # Initialize database connection
    db_settings = get_database_settings()
    engine = init_db(str(db_settings.DATABASE_URL))
    session_factory = get_session(engine)
    session = session_factory()
    db_manager = DatabaseManager(session)

    # Initialize tools
    sentiment_analyzer = SentimentAnalysisTool()
    sentiment_tracker = SentimentTracker(db_manager)
    visualizer = OpinionVisualizerTool(db_manager)

    # Sample articles with different sentiment profiles
    articles = [
        {
            "url": "https://example.com/climate-breakthrough",
            "title": "Renewable Energy Breakthrough Brings Hope",
            "content": """Scientists have made an amazing breakthrough in renewable energy technology. 
            The new solar panels are incredibly efficient and could revolutionize clean energy production. 
            This is excellent news for the fight against climate change.""",
            "source": "Science News",
            "published_at": datetime.now(timezone.utc) - timedelta(days=1)
        },
        {
            "url": "https://example.com/climate-crisis",
            "title": "Climate Crisis Worsens as Governments Fail to Act",
            "content": """The climate crisis continues to worsen as world leaders fail to take meaningful action. 
            The latest report shows terrible consequences for future generations. 
            Without immediate action, we face a disaster of unprecedented scale.""",
            "source": "Environmental Watch",
            "published_at": datetime.now(timezone.utc) - timedelta(days=2)
        },
        {
            "url": "https://example.com/politics-mixed",
            "title": "Mayor's Leadership Under Scrutiny",
            "content": """Mayor Smith has made some good decisions for the city, but recent controversies 
            have raised serious concerns. While the infrastructure improvements are excellent, 
            the handling of the budget crisis has been poor.""",
            "source": "Local News",
            "published_at": datetime.now(timezone.utc) - timedelta(days=3)
        }
    ]

    print("\n=== Analyzing Sample Articles ===\n")

    # Add articles to database and analyze them
    for article_data in articles:
        # Add article to database
        article = db_manager.add_article(article_data)
        print(f"\nAnalyzing article: {article.title}")
        
        # Perform sentiment analysis
        sentiment_results = sentiment_analyzer.analyze_article(db_manager, article.id)
        
        # Print results
        print(f"Document Sentiment: {sentiment_results['document_sentiment']:.2f}")
        print(f"Document Magnitude: {sentiment_results['document_magnitude']:.2f}")
        
        print("\nEntity Sentiments:")
        for entity, sentiment in sentiment_results['entity_sentiments'].items():
            print(f"  {entity}: {sentiment:.2f}")
        
        print("\nTopic Sentiments:")
        for topic, sentiment in sentiment_results['topic_sentiments'].items():
            print(f"  {topic}: {sentiment:.2f}")

    # Demonstrate trend analysis
    print("\n=== Analyzing Sentiment Trends ===\n")
    
    # Get sentiment trends for different time periods
    start_date = datetime.now(timezone.utc) - timedelta(days=7)
    end_date = datetime.now(timezone.utc)
    
    trends = sentiment_tracker.get_sentiment_by_period(
        start_date=start_date,
        end_date=end_date,
        time_interval="day",
        topics=["climate change", "politics"]
    )
    
    print("Sentiment Trends:")
    for period, period_data in trends.items():
        print(f"\nPeriod: {period}")
        for topic, topic_data in period_data.items():
            print(f"  {topic}:")
            print(f"    Average Sentiment: {topic_data['avg_sentiment']:.2f}")
            print(f"    Article Count: {topic_data['article_count']}")
            print(f"    Distribution: {topic_data['sentiment_distribution']}")

    # Demonstrate visualization
    print("\n=== Generating Visualizations ===\n")
    
    # Generate HTML report
    html_report = visualizer.generate_html_report(
        start_date=start_date,
        end_date=end_date,
        topics=["climate change", "politics"]
    )
    
    # Save report to file
    with open("sentiment_analysis_report.html", "w") as f:
        f.write(html_report)
    
    print("HTML report generated: sentiment_analysis_report.html")

    # Clean up
    session.close()


if __name__ == "__main__":
    asyncio.run(analyze_sample_articles()) 