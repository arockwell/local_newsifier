#!/usr/bin/env python
"""Script to run the news trend analysis flow."""

import argparse
import sys

from src.local_newsifier.flows.trend_analysis_flow import NewsTrendAnalysisFlow, ReportFormat
from src.local_newsifier.models.trend import TimeFrame, TrendAnalysisConfig


def main():
    """Run the news trend analysis flow with command line options."""
    parser = argparse.ArgumentParser(description="Run news trend analysis")

    # Time frame options
    parser.add_argument(
        "--time-frame",
        choices=["DAY", "WEEK", "MONTH", "QUARTER", "YEAR"],
        default="WEEK",
        help="Time frame for analysis (default: WEEK)",
    )

    parser.add_argument(
        "--lookback",
        type=int,
        default=4,
        help="Number of time periods to look back (default: 4)",
    )

    # Entity filtering
    parser.add_argument(
        "--entities",
        nargs="+",
        default=["PERSON", "ORG", "GPE"],
        help="Entity types to analyze (default: PERSON ORG GPE)",
    )

    # Statistical parameters
    parser.add_argument(
        "--min-articles",
        type=int,
        default=3,
        help="Minimum articles for a trend (default: 3)",
    )

    parser.add_argument(
        "--significance",
        type=float,
        default=1.5,
        help="Significance threshold (z-score) (default: 1.5)",
    )

    parser.add_argument(
        "--topic-limit",
        type=int,
        default=20,
        help="Maximum number of topics to track (default: 20)",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        default="trend_output",
        help="Directory for output files (default: trend_output)",
    )

    parser.add_argument(
        "--format",
        choices=["markdown", "json", "text"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    parser.add_argument(
        "--output",
        help="Output filename (default: auto-generated)",
    )

    # Parse arguments
    args = parser.parse_args()

    # Create configuration
    config = TrendAnalysisConfig(
        time_frame=TimeFrame(args.time_frame),
        min_articles=args.min_articles,
        min_confidence=0.6,
        entity_types=args.entities,
        significance_threshold=args.significance,
        topic_limit=args.topic_limit,
        lookback_periods=args.lookback,
    )

    # Initialize and run the flow
    flow = NewsTrendAnalysisFlow(config=config, output_dir=args.output_dir)

    print(f"Starting trend analysis with {args.time_frame} time frame...")

    # Run the flow
    state = flow.run_analysis(config=config, report_format=ReportFormat(args.format))

    # Print results
    if state.error:
        print(f"Error during analysis: {state.error}")
        sys.exit(1)

    print(f"Analysis completed. Found {len(state.detected_trends)} trends.")

    if state.report_path:
        print(f"Report saved to: {state.report_path}")

    # Print a summary of top trends
    if state.detected_trends:
        print("\nTop trends:")
        sorted_trends = sorted(
            state.detected_trends, key=lambda t: t.confidence_score, reverse=True
        )[:5]
        for i, trend in enumerate(sorted_trends, 1):
            print(f"{i}. {trend.name} - {trend.description}")


if __name__ == "__main__":
    main()
