"""Demo script for testing the news investigation crew."""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from local_newsifier.config.database import get_db_session
from local_newsifier.database.manager import DatabaseManager
from local_newsifier.crews.investigation_crew import NewsInvestigationCrew

def run_investigation_demo():
    """Run a demo investigation using the news investigation crew."""
    # Initialize database session
    Session = get_db_session()
    session = Session()
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(session)
        
        # Create investigation crew
        crew = NewsInvestigationCrew(db_manager=db_manager)
        
        print("Starting investigation...")
        
        # Run investigation on local development
        investigation = crew.investigate(initial_topic="Local Development Projects")
        
        print("\nInvestigation Results:")
        print(f"Topic: {investigation.topic}")
        print("\nKey Findings:")
        for finding in investigation.key_findings:
            print(f"- {finding}")
        
        print(f"\nEvidence Score: {investigation.evidence_score}/10")
        
        print("\nEntities of Interest:")
        for entity in investigation.entities_of_interest:
            print(f"- {entity}")
        
        print("\nEntity Connections:")
        for connection in investigation.connections:
            print(f"- {connection['source_entity']} -> {connection['target_entity']}")
            print(f"  Type: {connection['relationship_type']}")
            print(f"  Confidence: {connection['confidence_score']}")
        
        # Generate reports in different formats
        print("\nGenerating reports...")
        
        # Markdown report
        md_path = crew.generate_report(investigation, output_format="md")
        print(f"Markdown report saved to: {md_path}")
        
        # HTML report
        html_path = crew.generate_report(investigation, output_format="html")
        print(f"HTML report saved to: {html_path}")
        
    finally:
        session.close()

if __name__ == "__main__":
    run_investigation_demo() 