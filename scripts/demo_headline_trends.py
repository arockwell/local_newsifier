#!/usr/bin/env python3
"""
Demo script for headline trend analysis.

This script demonstrates how to use the HeadlineTrendFlow to analyze trends
in article headlines over time.
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