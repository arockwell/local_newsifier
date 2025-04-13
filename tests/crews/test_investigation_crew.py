"""Test suite for the NewsInvestigationCrew."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from crewai import Agent, Crew, Task

from local_newsifier.crews.investigation_crew import (
    EntityAppearancesTool,
    EntityConnectionsTool,
    EntityContextTool,
    EntityResolveTool,
    FileWriterTool,
    InvestigationResult,
    NewsInvestigationCrew,
)
from local_newsifier.models.entity_tracking import EntityConnection


@pytest.fixture
def mock_database_manager():
    """Create a mock database manager."""
    return MagicMock()


@pytest.fixture
def mock_entity_resolver():
    """Create a mock entity resolver."""
    return MagicMock(name="EntityResolver()")


@pytest.fixture
def mock_entity_tracker():
    """Create a mock entity tracker."""
    from local_newsifier.tools.entity_tracker import EntityTracker
    tracker = MagicMock(spec=EntityTracker)
    return tracker


@pytest.fixture
def mock_context_analyzer():
    """Create a mock context analyzer."""
    from local_newsifier.tools.context_analyzer import ContextAnalyzer
    return ContextAnalyzer(model_name="en_core_web_sm")


@pytest.fixture
def mock_file_writer():
    """Create a mock file writer."""
    return MagicMock(name="FileWriter()")


@pytest.fixture
def mock_crewai_agent():
    """Create a mock crewai agent."""
    return MagicMock(name="Agent")


@pytest.fixture
def mock_crewai_crew():
    """Create a mock crewai crew."""
    return MagicMock(name="Crew")


@pytest.fixture
def mock_crewai_task():
    """Create a mock crewai Task."""
    with patch("local_newsifier.crews.investigation_crew.crewai.Task") as mock:
        yield mock


@pytest.fixture
def investigation_crew(
    mock_database_manager,
    mock_entity_resolver,
    mock_entity_tracker,
    mock_context_analyzer,
    mock_file_writer,
    mock_crewai_agent,
    mock_crewai_crew,
):
    """Create a NewsInvestigationCrew with mocked dependencies."""
    with patch("local_newsifier.crews.investigation_crew.EntityResolver", return_value=mock_entity_resolver), \
         patch("local_newsifier.crews.investigation_crew.EntityTracker", return_value=mock_entity_tracker), \
         patch("local_newsifier.crews.investigation_crew.ContextAnalyzer", return_value=mock_context_analyzer), \
         patch("local_newsifier.crews.investigation_crew.FileWriter", return_value=mock_file_writer), \
         patch("local_newsifier.crews.investigation_crew.Agent", mock_crewai_agent), \
         patch("local_newsifier.crews.investigation_crew.Crew", return_value=mock_crewai_crew):
        crew = NewsInvestigationCrew(db_manager=mock_database_manager)
        return crew


class TestNewsInvestigationCrew:
    """Tests for the NewsInvestigationCrew class."""

    def test_initialization(
        self, investigation_crew, mock_crewai_agent, mock_crewai_crew
    ):
        """Test that the crew is initialized with the correct dependencies."""
        assert investigation_crew.db_manager is not None
        assert investigation_crew.entity_resolver is not None
        assert investigation_crew.entity_tracker is not None
        assert investigation_crew.context_analyzer is not None
        assert investigation_crew.file_writer is not None
        
        # Verify that crewai components were created
        assert mock_crewai_agent.call_count == 3  # Three agents should be created
        assert mock_crewai_crew.call_count == 1  # One crew should be created

    def test_investigate_with_topic(
        self, investigation_crew, mock_crewai_crew, mock_crewai_task, mock_entity_tracker
    ):
        """Test investigating with a provided topic."""
        # Perform investigation
        result = investigation_crew.investigate(initial_topic="Local real estate development")
        
        # Verify crew was used
        assert investigation_crew.crew.kickoff.called
        
        # Check that tasks were created with the right topic
        assert mock_crewai_task.call_count == 3
        assert "Local real estate development" in mock_crewai_task.call_args_list[0].kwargs["description"]
        
        # Verify the return value
        assert isinstance(result, InvestigationResult)
        assert result.topic == "Local real estate development"
        assert len(result.connections) > 0
        assert len(result.key_findings) > 0
        assert isinstance(result.evidence_score, int)
        assert 1 <= result.evidence_score <= 10

        # Verify entity tracker was called
        mock_entity_tracker.get_entity_connections.assert_called_once_with(
            entity_name="Local real estate development", limit=10
        )

    def test_investigate_without_topic(
        self, investigation_crew, mock_crewai_crew, mock_crewai_task
    ):
        """Test investigating without a provided topic."""
        # Perform investigation
        result = investigation_crew.investigate()
        
        # Verify crew was used
        assert investigation_crew.crew.kickoff.called
        
        # Check that tasks were created for auto-discovery
        assert mock_crewai_task.call_count == 3
        assert "Identify potential investigation topics" in mock_crewai_task.call_args_list[0].kwargs["description"]
        
        # Verify the return value
        assert isinstance(result, InvestigationResult)
        assert "Auto-determined" in result.topic
        assert len(result.connections) > 0
        assert len(result.key_findings) > 0

    def test_generate_report_markdown(self, investigation_crew, mock_file_writer):
        """Test generating a markdown report."""
        # Create test investigation result
        investigation = InvestigationResult(
            topic="Test Investigation",
            key_findings=["Finding 1", "Finding 2"],
            evidence_score=8,
            connections=[
                EntityConnection(
                    source_entity="Entity A",
                    target_entity="Entity B",
                    relationship_type="connection",
                    confidence_score=0.9,
                    source_article_ids=[1],
                )
            ],
            entities_of_interest=["Entity A", "Entity B"],
        )
        
        # Generate report
        report_path = investigation_crew.generate_report(
            investigation=investigation,
            output_format="md",
            output_path="test_report.md"
        )
        
        # Verify file writer was called with correct content
        assert mock_file_writer.write_file.called
        call_args = mock_file_writer.write_file.call_args
        assert call_args[0][0] == "test_report.md"
        
        report_content = call_args[0][1]
        assert "# Investigation Report: Test Investigation" in report_content
        assert "Finding 1" in report_content
        assert "Finding 2" in report_content
        assert "Evidence Strength: 8/10" in report_content
        assert "Entity A" in report_content
        assert "Entity B" in report_content
        
        assert report_path == "test_report.md"

    def test_generate_report_html(self, investigation_crew, mock_file_writer):
        """Test generating an HTML report."""
        # Create test investigation result
        investigation = InvestigationResult(
            topic="Test Investigation",
            key_findings=["Finding 1", "Finding 2"],
            evidence_score=8,
            connections=[
                EntityConnection(
                    source_entity="Entity A",
                    target_entity="Entity B",
                    relationship_type="connection",
                    confidence_score=0.9,
                    source_article_ids=[1],
                )
            ],
            entities_of_interest=["Entity A", "Entity B"],
        )
        
        # Generate report
        report_path = investigation_crew.generate_report(
            investigation=investigation,
            output_format="html",
            output_path="test_report.html"
        )
        
        # Verify file writer was called with correct content
        assert mock_file_writer.write_file.called
        call_args = mock_file_writer.write_file.call_args
        assert call_args[0][0] == "test_report.html"
        
        report_content = call_args[0][1]
        assert "<title>Investigation Report: Test Investigation</title>" in report_content
        assert "<li>Finding 1</li>" in report_content
        assert "<li>Finding 2</li>" in report_content
        assert "Evidence Strength: 8/10" in report_content
        assert "Entity A" in report_content
        assert "Entity B" in report_content
        
        assert report_path == "test_report.html"

    def test_generate_report_default_path(self, investigation_crew, mock_file_writer):
        """Test generating a report with default path."""
        # Create test investigation result
        investigation = InvestigationResult(
            topic="Test Topic",
            key_findings=["Finding"],
            evidence_score=5,
            connections=[],
            entities_of_interest=[],
        )
        
        # Generate report without specifying path
        report_path = investigation_crew.generate_report(investigation)
        
        # Verify file writer was called with default path
        assert mock_file_writer.write_file.called
        expected_path = "reports/investigation_Test_Topic.md"
        assert mock_file_writer.write_file.call_args[0][0] == expected_path
        assert report_path == expected_path

    def test_extract_entities_from_connections(self, investigation_crew):
        """Test extracting unique entities from connections."""
        # Create test connections
        connections = [
            EntityConnection(
                source_entity="Entity A",
                target_entity="Entity B",
                relationship_type="type1",
                confidence_score=0.8,
                source_article_ids=[1],
            ),
            EntityConnection(
                source_entity="Entity B",
                target_entity="Entity C",
                relationship_type="type2",
                confidence_score=0.7,
                source_article_ids=[2],
            ),
            EntityConnection(
                source_entity="Entity A",
                target_entity="Entity C",
                relationship_type="type3",
                confidence_score=0.9,
                source_article_ids=[3],
            ),
        ]
        
        # Extract entities
        entities = investigation_crew._extract_entities_from_connections(connections)
        
        # Verify result
        assert set(entities) == {"Entity A", "Entity B", "Entity C"}
        assert len(entities) == 3  # No duplicates