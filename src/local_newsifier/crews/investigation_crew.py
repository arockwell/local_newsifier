"""News investigation crew for analyzing connections in local news articles."""

from typing import Dict, List, Optional, Tuple, Union

import crewai
from pydantic import BaseModel, Field

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.entity_tracking import EntityConnection
from local_newsifier.tools.context_analyzer import ContextAnalyzer
from local_newsifier.tools.entity_resolver import EntityResolver
from local_newsifier.tools.entity_tracker import EntityTracker
from local_newsifier.tools.file_writer import FileWriter


class InvestigationResult(BaseModel):
    """A model representing the results of a news investigation."""

    topic: str = Field(description="The topic of the investigation")
    key_findings: List[str] = Field(description="Key findings from the investigation")
    evidence_score: int = Field(
        description="Score from 1-10 indicating the strength of evidence"
    )
    connections: List[EntityConnection] = Field(
        description="Connections identified between entities", default_factory=list
    )
    entities_of_interest: List[str] = Field(
        description="List of key entities relevant to the investigation",
        default_factory=list,
    )
    investigation_metadata: Dict[str, Union[str, int, float]] = Field(
        description="Additional metadata about the investigation",
        default_factory=dict,
    )


class NewsInvestigationCrew:
    """A crew for investigating relationships and patterns in local news articles."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize the news investigation crew.

        Args:
            db_manager: Optional database manager for persistence.
                        If None, a new one will be created.
        """
        self.db_manager = db_manager or DatabaseManager()
        self.entity_resolver = EntityResolver()
        self.entity_tracker = EntityTracker(db_manager=self.db_manager)
        self.context_analyzer = ContextAnalyzer()
        self.file_writer = FileWriter()

        # Initialize the crew components
        self._initialize_crew()

    def _initialize_crew(self) -> None:
        """Initialize the crew with necessary agents and tasks."""
        # Define the crew's agents
        self.researcher = crewai.Agent(
            role="News Researcher",
            goal="Find relevant articles and extract key information",
            backstory="Expert at finding patterns in news coverage",
            tools=[
                self.entity_tracker.get_entity_appearances,
                self.entity_tracker.get_entity_connections,
            ],
        )

        self.analyst = crewai.Agent(
            role="Investigation Analyst",
            goal="Analyze connections between entities and identify patterns",
            backstory="Skilled at finding hidden connections in complex data",
            tools=[
                self.context_analyzer.analyze_entity_context,
                self.entity_resolver.resolve_entity,
            ],
        )

        self.reporter = crewai.Agent(
            role="Investigation Reporter",
            goal="Compile findings into clear, evidence-based reports",
            backstory="Experienced investigative journalist skilled at presenting complex findings",
            tools=[self.file_writer.write_file],
        )

        # Create the crew
        self.crew = crewai.Crew(
            agents=[self.researcher, self.analyst, self.reporter],
            tasks=[],  # Tasks will be defined per investigation
            verbose=True,
        )

    def investigate(
        self, initial_topic: Optional[str] = None
    ) -> InvestigationResult:
        """Conduct an investigation into local news patterns and connections.

        Args:
            initial_topic: Optional topic to investigate. If None, the crew will
                           determine a topic based on data analysis.

        Returns:
            InvestigationResult: The results of the investigation.
        """
        # Define investigation tasks based on initial topic
        if initial_topic:
            research_task = crewai.Task(
                description=f"Research articles related to '{initial_topic}' and identify key entities",
                agent=self.researcher,
                expected_output="List of relevant entities and their appearances",
            )
        else:
            research_task = crewai.Task(
                description="Identify potential investigation topics based on entity analysis",
                agent=self.researcher,
                expected_output="Potential investigation topics with supporting evidence",
            )

        analysis_task = crewai.Task(
            description="Analyze connections between identified entities and evaluate evidence",
            agent=self.analyst,
            expected_output="Analysis of entity connections with evidence score",
            context=[research_task],
        )

        report_task = crewai.Task(
            description="Compile investigation findings into a structured result",
            agent=self.reporter,
            expected_output="Structured investigation findings with key insights",
            context=[research_task, analysis_task],
        )

        # Set up crew tasks for this investigation
        self.crew.tasks = [research_task, analysis_task, report_task]

        # Run the investigation and process results
        result = self.crew.kickoff()

        # Process the result into an InvestigationResult object
        # In a real implementation, this would parse the result into the proper structure
        # For now, we'll create a simplified example
        topic = initial_topic or "Auto-determined investigation topic"
        connections = self.entity_tracker.get_entity_connections(
            entity_name=topic, limit=10
        )

        investigation_result = InvestigationResult(
            topic=topic,
            key_findings=["Finding 1 based on analysis", "Finding 2 based on analysis"],
            evidence_score=7,  # Example score
            connections=connections,
            entities_of_interest=self._extract_entities_from_connections(connections),
        )

        return investigation_result

    def generate_report(
        self,
        investigation: InvestigationResult,
        output_format: str = "md",
        output_path: Optional[str] = None,
    ) -> str:
        """Generate a detailed report from investigation results.

        Args:
            investigation: The investigation result to generate a report for
            output_format: Format for the output ('md', 'pdf', 'html')
            output_path: Path to save the report, if None a default path is used

        Returns:
            str: Path to the generated report file
        """
        if output_path is None:
            output_path = f"reports/investigation_{investigation.topic.replace(' ', '_')}.{output_format}"

        # Create report content
        report_content = self._create_report_content(investigation, output_format)

        # Write the report to a file
        self.file_writer.write_file(output_path, report_content)

        return output_path

    def _create_report_content(
        self, investigation: InvestigationResult, output_format: str
    ) -> str:
        """Create the content for the investigation report.

        Args:
            investigation: The investigation results
            output_format: Format for the output

        Returns:
            str: The formatted report content
        """
        if output_format == "md":
            return self._create_markdown_report(investigation)
        elif output_format == "html":
            return self._create_html_report(investigation)
        else:
            # Default to markdown
            return self._create_markdown_report(investigation)

    def _create_markdown_report(self, investigation: InvestigationResult) -> str:
        """Create a markdown report from investigation results.

        Args:
            investigation: The investigation results

        Returns:
            str: Markdown-formatted report
        """
        report = f"# Investigation Report: {investigation.topic}\n\n"
        report += "## Key Findings\n\n"
        
        for i, finding in enumerate(investigation.key_findings, 1):
            report += f"{i}. {finding}\n"
        
        report += f"\n## Evidence Strength: {investigation.evidence_score}/10\n\n"
        
        report += "## Entity Connections\n\n"
        for connection in investigation.connections:
            report += f"- {connection.source_entity} → {connection.target_entity}: {connection.relationship_type}\n"
        
        report += "\n## Entities of Interest\n\n"
        for entity in investigation.entities_of_interest:
            report += f"- {entity}\n"
            
        return report

    def _create_html_report(self, investigation: InvestigationResult) -> str:
        """Create an HTML report from investigation results.

        Args:
            investigation: The investigation results

        Returns:
            str: HTML-formatted report
        """
        # Simple HTML report template
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Investigation Report: {investigation.topic}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #444; margin-top: 30px; }}
        ul {{ margin-top: 10px; }}
    </style>
</head>
<body>
    <h1>Investigation Report: {investigation.topic}</h1>
    
    <h2>Key Findings</h2>
    <ul>
"""
        
        for finding in investigation.key_findings:
            html += f"        <li>{finding}</li>\n"
            
        html += f"""    </ul>
    
    <h2>Evidence Strength: {investigation.evidence_score}/10</h2>
    
    <h2>Entity Connections</h2>
    <ul>
"""
        
        for connection in investigation.connections:
            html += f"        <li>{connection.source_entity} → {connection.target_entity}: {connection.relationship_type}</li>\n"
            
        html += """    </ul>
    
    <h2>Entities of Interest</h2>
    <ul>
"""
        
        for entity in investigation.entities_of_interest:
            html += f"        <li>{entity}</li>\n"
            
        html += """    </ul>
</body>
</html>"""
        
        return html

    def _extract_entities_from_connections(
        self, connections: List[EntityConnection]
    ) -> List[str]:
        """Extract unique entity names from connections.

        Args:
            connections: List of entity connections

        Returns:
            List[str]: Unique entity names
        """
        entities = set()
        for connection in connections:
            entities.add(connection.source_entity)
            entities.add(connection.target_entity)
        return list(entities)