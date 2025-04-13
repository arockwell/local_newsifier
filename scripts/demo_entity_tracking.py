#!/usr/bin/env python3

"""
Demo script for entity tracking workflow.

This script demonstrates the entity tracking functionality by processing
sample news articles and showing entity tracking dashboard.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.local_newsifier.config.database import get_database, get_db_session
from src.local_newsifier.database.manager import DatabaseManager
from src.local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
from src.local_newsifier.models.database import ArticleCreate
from src.local_newsifier.models.entity_tracking import CanonicalEntityCreate


def create_sample_articles(db_manager: DatabaseManager) -> List[Dict]:
    """Create sample articles for the demo."""
    articles = [
        {
            "url": "https://example.com/biden-policy",
            "title": "Biden Announces New Policy Initiative",
            "content": """
                President Joe Biden announced a new policy initiative today at the White House.
                The President outlined his vision for infrastructure investment across the country.
                Vice President Kamala Harris was also present at the announcement.
                Speaker Nancy Pelosi praised the initiative, while Senator Mitch McConnell expressed concerns.
            """,
            "published_at": datetime.now(timezone.utc) - timedelta(days=3),
            "status": "analyzed"
        },
        {
            "url": "https://example.com/harris-speech",
            "title": "Harris Delivers Speech on Climate Change",
            "content": """
                Vice President Kamala Harris delivered a major speech on climate change today.
                Harris emphasized the administration's commitment to reducing carbon emissions.
                The Vice President cited research from experts in the field.
                President Biden's previous statements on climate were also referenced.
            """,
            "published_at": datetime.now(timezone.utc) - timedelta(days=2),
            "status": "analyzed"
        },
        {
            "url": "https://example.com/biden-mcconnell",
            "title": "Biden and McConnell Discuss Infrastructure",
            "content": """
                President Joe Biden met with Senator Mitch McConnell to discuss the infrastructure bill.
                The President and the Senate Minority Leader had what sources described as a productive meeting.
                Biden later spoke to reporters about the potential for bipartisan cooperation.
                McConnell said he remains concerned about the cost of the proposal.
            """,
            "published_at": datetime.now(timezone.utc) - timedelta(days=1),
            "status": "analyzed"
        },
        {
            "url": "https://example.com/pelosi-statement",
            "title": "Pelosi Issues Statement on Budget Negotiations",
            "content": """
                Speaker Nancy Pelosi issued a statement regarding ongoing budget negotiations.
                Pelosi expressed confidence that an agreement would be reached before the deadline.
                The Speaker said she had spoken with President Biden earlier in the day.
                Senate Majority Leader Chuck Schumer also released a statement supporting the negotiations.
            """,
            "published_at": datetime.now(timezone.utc),
            "status": "analyzed"
        },
    ]
    
    created_articles = []
    for article_data in articles:
        article = ArticleCreate(
            url=article_data["url"],
            title=article_data["title"],
            content=article_data["content"],
            published_at=article_data["published_at"],
            status=article_data["status"]
        )
        created_article = db_manager.create_article(article)
        created_articles.append(created_article)
        print(f"Created article: {created_article.title}")
    
    return created_articles


def display_dashboard(dashboard: Dict) -> None:
    """Display entity tracking dashboard in a formatted way."""
    print("\n" + "=" * 80)
    print("ENTITY TRACKING DASHBOARD")
    print("=" * 80)
    
    # Print date range
    start_date = dashboard["date_range"]["start"].strftime("%Y-%m-%d")
    end_date = dashboard["date_range"]["end"].strftime("%Y-%m-%d")
    print(f"\nDate Range: {start_date} to {end_date} ({dashboard['date_range']['days']} days)")
    
    # Print summary
    print(f"\nTotal Entities: {dashboard['entity_count']}")
    print(f"Total Mentions: {dashboard['total_mentions']}")
    
    # Print entities
    print("\nTop Entities by Mention Count:")
    print("-" * 80)
    print(f"{'Name':<30} {'Type':<10} {'Mentions':<10} {'First Seen':<20} {'Last Seen':<20}")
    print("-" * 80)
    
    for entity in dashboard["entities"]:
        first_seen = entity["first_seen"].strftime("%Y-%m-%d %H:%M") if entity["first_seen"] else "N/A"
        last_seen = entity["last_seen"].strftime("%Y-%m-%d %H:%M") if entity["last_seen"] else "N/A"
        
        print(f"{entity['name']:<30} {entity['type']:<10} {entity['mention_count']:<10} {first_seen:<20} {last_seen:<20}")
    
    # Print detailed info for top entity
    if dashboard["entities"]:
        top_entity = dashboard["entities"][0]
        print("\n" + "-" * 80)
        print(f"DETAILED VIEW: {top_entity['name']}")
        print("-" * 80)
        
        # Print timeline
        print("\nRecent Mentions:")
        for mention in top_entity.get("timeline", []):
            date = mention["date"].strftime("%Y-%m-%d %H:%M")
            title = mention["article"]["title"]
            sentiment = f"Sentiment: {mention['sentiment_score']:.2f}"
            
            print(f"  {date} - {title} ({sentiment})")
            print(f"  Context: \"{mention['context']}\"")
            print()
        
        # Print sentiment trend
        print("\nSentiment Trend:")
        for point in top_entity.get("sentiment_trend", []):
            date = point["date"].strftime("%Y-%m-%d")
            sentiment = f"{point['avg_sentiment']:.2f}"
            count = point["mention_count"]
            
            print(f"  {date}: {sentiment} (from {count} mentions)")
    
    print("\n" + "=" * 80)


def main():
    """Run the entity tracking demo."""
    parser = argparse.ArgumentParser(description="Demo for entity tracking workflow")
    parser.add_argument("--env-file", default=".env", help="Environment file path")
    parser.add_argument("--days", type=int, default=30, help="Number of days for dashboard")
    parser.add_argument("--json", action="store_true", help="Output dashboard as JSON")
    args = parser.parse_args()
    
    # Initialize database
    engine = get_database(args.env_file)
    session_factory = get_db_session(args.env_file)
    session = session_factory()
    
    try:
        db_manager = DatabaseManager(session)
        
        # Create sample articles
        print("Creating sample articles...")
        create_sample_articles(db_manager)
        
        # Initialize entity tracking flow
        entity_tracking_flow = EntityTrackingFlow(db_manager)
        
        # Process articles
        print("\nProcessing articles for entity tracking...")
        results = entity_tracking_flow.process_new_articles()
        print(f"Processed {len(results)} articles")
        
        for result in results:
            print(f"  Article: {result['title']}")
            print(f"  Entities found: {result['entity_count']}")
            print(f"  Entity names: {', '.join(e['canonical_name'] for e in result['entities'])}")
            print()
        
        # Generate dashboard
        print("Generating entity tracking dashboard...")
        dashboard = entity_tracking_flow.get_entity_dashboard(days=args.days)
        
        # Display dashboard
        if args.json:
            # Convert datetime objects to strings for JSON serialization
            dashboard_json = json.dumps(dashboard, default=lambda o: o.isoformat() if isinstance(o, datetime) else None)
            print(dashboard_json)
        else:
            display_dashboard(dashboard)
        
    finally:
        session.close()


if __name__ == "__main__":
    main()