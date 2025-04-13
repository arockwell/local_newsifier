#!/usr/bin/env python3
"""Demo script for the News Investigation Crew."""

import argparse
import os

from local_newsifier.config import settings
from local_newsifier.config.database import get_database_settings, get_db_session
from local_newsifier.crews.investigation_crew import NewsInvestigationCrew
from local_newsifier.database.manager import DatabaseManager


def main():
    """Run the demo script."""
    parser = argparse.ArgumentParser(description="Run a news investigation")
    parser.add_argument(
        "--topic",
        help="Specific topic to investigate (optional)",
        default=None,
    )
    parser.add_argument(
        "--output-format",
        help="Output format for report (md, html, pdf)",
        choices=["md", "html", "pdf"],
        default="md",
    )
    parser.add_argument(
        "--output-path",
        help="Path to save investigation report",
        default=None,
    )
    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    # Initialize database
    Session = get_db_session()
    session = Session()
    db_manager = DatabaseManager(session)

    # Initialize the investigation crew
    print("Initializing News Investigation Crew...")
    crew = NewsInvestigationCrew(db_manager=db_manager)

    try:
        # Start investigation
        if args.topic:
            print(f"Starting investigation on topic: {args.topic}")
            investigation = crew.investigate(initial_topic=args.topic)
        else:
            print("Starting self-directed investigation...")
            investigation = crew.investigate()

        # Print investigation results
        print("\nInvestigation Results:")
        print(f"Topic: {investigation.topic}")
        print(f"Evidence Strength: {investigation.evidence_score}/10")
        print(f"Connections Identified: {len(investigation.connections)}")
        
        print("\nKey Findings:")
        for i, finding in enumerate(investigation.key_findings, 1):
            print(f"{i}. {finding}")
        
        # Generate and save report
        report_path = crew.generate_report(
            investigation=investigation,
            output_format=args.output_format,
            output_path=args.output_path,
        )
        print(f"\nFull report saved to: {report_path}")
    finally:
        session.close()


if __name__ == "__main__":
    main()