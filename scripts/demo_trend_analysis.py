#!/usr/bin/env python
"""Demonstration script for using the consolidated AnalysisService.

This script showcases the capabilities of the consolidated AnalysisService
and TrendAnalyzer, which simplify trend analysis operations by providing
a unified interface.

Usage:
    poetry run python scripts/demo_trend_analysis.py [--days DAYS]

Options:
    --days DAYS    Number of days of data to analyze [default: 30]
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
import json
import logging

from sqlmodel import Session, select

from local_newsifier.database.engine import get_engine
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.services.analysis_service import AnalysisService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


def format_trend_data(trend_data):
    """Format trend data for display.
    
    Args:
        trend_data: Trend data to format
        
    Returns:
        Formatted string
    """
    if "error" in trend_data:
        return f"Error: {trend_data['error']}"
        
    output = []
    
    # Add trending terms
    output.append(f"\n{'=' * 40}\nTRENDING TERMS\n{'=' * 40}")
    if trend_data["trending_terms"]:
        for i, term in enumerate(trend_data["trending_terms"], 1):
            output.append(
                f"{i}. {term['term']} (growth: {term['growth_rate']:.1f}x, "
                f"mentions: {term['total_mentions']})"
            )
    else:
        output.append("No trending terms detected")
        
    # Add overall top terms
    output.append(f"\n{'=' * 40}\nTOP TERMS OVERALL\n{'=' * 40}")
    if trend_data["overall_top_terms"]:
        for i, (term, count) in enumerate(trend_data["overall_top_terms"][:10], 1):
            output.append(f"{i}. {term} ({count} mentions)")
    else:
        output.append("No top terms found")
        
    # Add period counts
    output.append(f"\n{'=' * 40}\nARTICLES BY PERIOD\n{'=' * 40}")
    if trend_data["period_counts"]:
        periods = sorted(trend_data["period_counts"].keys())
        for period in periods:
            count = trend_data["period_counts"][period]
            output.append(f"{period}: {count} articles")
    else:
        output.append("No articles found in this period")
        
    return "\n".join(output)


def format_entity_trends(trends):
    """Format entity trends for display.
    
    Args:
        trends: Entity trends to format
        
    Returns:
        Formatted string
    """
    if not trends:
        return "No entity trends detected"
        
    output = []
    
    # Add trending entities
    output.append(f"\n{'=' * 40}\nTRENDING ENTITIES\n{'=' * 40}")
    
    for i, trend in enumerate(trends, 1):
        output.append(f"{i}. {trend.name} ({trend.trend_type.name})")
        output.append(f"   Confidence: {trend.confidence_score:.2f}")
        output.append(f"   Description: {trend.description}")
        
        if trend.entities:
            output.append(f"\n   Related Entities:")
            for entity in trend.entities[:5]:  # Show top 5 related entities
                output.append(f"   - {entity.text} ({entity.entity_type}): {entity.frequency} mentions")
                
        if trend.evidence:
            output.append(f"\n   Evidence Articles:")
            for evidence in trend.evidence[:3]:  # Show top 3 evidence articles
                output.append(f"   - {evidence.article_title}")
                if evidence.published_at:
                    output.append(f"     Published: {evidence.published_at.strftime('%Y-%m-%d')}")
                    
        output.append("")  # Add a blank line between trends
        
    return "\n".join(output)


def analyze_trends(days):
    """Analyze trends in articles from the last N days.
    
    Args:
        days: Number of days to analyze
        
    Returns:
        None
    """
    engine = get_engine()
    
    logger.info(f"Analyzing trends for the last {days} days")
    
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    
    # Check if we have articles in this time range
    with Session(engine) as session:
        article_count = session.exec(
            select(Article).where(
                Article.published_at >= start_date,
                Article.published_at <= end_date
            )
        ).all()
        
        if not article_count:
            logger.error(f"No articles found in the specified date range")
            logger.info("Please run the news pipeline first to fetch articles")
            sys.exit(1)
            
        logger.info(f"Found {len(article_count)} articles in the date range")
        
        # Create AnalysisService
        analysis_service = AnalysisService()
        
        # Analyze headline trends
        logger.info("Analyzing headline trends...")
        headline_trends = analysis_service.analyze_headline_trends(
            start_date=start_date,
            end_date=end_date,
            time_interval="day"
        )
        
        # Detect entity trends
        logger.info("Detecting entity trends...")
        entity_trends = analysis_service.detect_entity_trends(
            entity_types=["PERSON", "ORG", "GPE"],
            min_mentions=2
        )
        
        # Print results
        print("\n\n")
        print("=" * 80)
        print(f"TREND ANALYSIS RESULTS ({days} DAYS)")
        print("=" * 80)
        
        print("\n\nHEADLINE TRENDS")
        print("-" * 80)
        print(format_trend_data(headline_trends))
        
        print("\n\nENTITY TRENDS")
        print("-" * 80)
        print(format_entity_trends(entity_trends))
        
        logger.info("Analysis complete")


def main():
    """Run the demo script."""
    parser = argparse.ArgumentParser(description="Demonstrate trend analysis")
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days of data to analyze",
    )
    
    args = parser.parse_args()
    analyze_trends(args.days)


if __name__ == "__main__":
    main()
