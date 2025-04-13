#!/usr/bin/env python3
"""
Demo script for headline trend analysis.

This script demonstrates how to use the HeadlineTrendFlow to analyze trends
in article headlines over time.

The script will:
1. Connect to the database to retrieve article headlines
2. Group headlines by time periods (day, week, or month)
3. Extract significant keywords using NLP techniques
4. Identify trending terms by analyzing frequency changes over time
5. Generate a formatted report (text, markdown, or HTML)

Example usage:
    # Basic usage (analyzes last 30 days with daily intervals)
    python demo_headline_trends.py

    # Analyze recent headlines with weekly intervals
    python demo_headline_trends.py --days 90 --interval week

    # Analyze a specific date range
    python demo_headline_trends.py --start-date 2023-01-01 --end-date 2023-03-31 --interval month

    # Generate a markdown report and save to file
    python demo_headline_trends.py --format markdown --output trends.md

    # Generate an HTML report with more terms
    python demo_headline_trends.py --format html --top 30 --output trends.html
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta

from local_newsifier.flows.analysis import HeadlineTrendFlow


def main():
    """Run the headline trend analysis demo."""
    parser = argparse.ArgumentParser(description="Headline trend analysis demo")
    parser.add_argument(
        "--days", type=int, default=30, help="Number of days to analyze (default: 30)"
    )
    parser.add_argument(
        "--interval",
        choices=["day", "week", "month"],
        default="day",
        help="Time interval for analysis (default: day)"
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "html"],
        default="text",
        help="Report format (default: text)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="Number of top terms to include (default: 20)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for analysis (YYYY-MM-DD), overrides --days"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for analysis (YYYY-MM-DD), defaults to today if start-date is specified"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Initialize the flow
    flow = HeadlineTrendFlow()
    
    try:
        # Analyze trends
        if args.start_date:
            # Parse dates
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            if args.end_date:
                end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
            else:
                end_date = datetime.now()
                
            print(f"Analyzing headlines from {start_date.date()} to {end_date.date()}...")
            results = flow.analyze_date_range(
                start_date=start_date,
                end_date=end_date,
                interval=args.interval,
                top_n=args.top
            )
        else:
            print(f"Analyzing headlines for the past {args.days} days...")
            results = flow.analyze_recent_trends(
                days_back=args.days,
                interval=args.interval,
                top_n=args.top
            )
        
        # Generate report
        report = flow.generate_report(results, format_type=args.format)
        
        # Output report
        if args.output:
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print("\n" + report)
            
    except Exception as e:
        logging.error(f"Error during analysis: {e}", exc_info=args.verbose)
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())