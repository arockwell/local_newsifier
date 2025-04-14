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
from local_newsifier.tools.entity_tracker import EntityTracker
from local_newsifier.tools.entity_resolver import EntityResolver
from local_newsifier.tools.context_analyzer import ContextAnalyzer
from local_newsifier.tools.file_writer import FileWriter


@pytest.fixture
def mock_database_manager():
    """Create a mock database manager."""
    return MagicMock()


@pytest.fixture
def mock_entity_resolver():
    """Create a mock entity resolver."""
    return MagicMock(spec=EntityResolver)


@pytest.fixture
def mock_entity_tracker():
    """Create a mock entity tracker."""
    return MagicMock(spec=EntityTracker)


@pytest.fixture
def mock_context_analyzer():
    """Create a mock context analyzer."""
    return MagicMock(spec=ContextAnalyzer)


@pytest.fixture
def mock_file_writer():
    """Create a mock file writer."""
    mock = MagicMock(spec=FileWriter)
    mock.write_file = MagicMock()
    return mock


@pytest.fixture
def mock_crewai_agent():
    """Create a mock crewai agent."""
    with patch("local_newsifier.crews.investigation_crew.Agent") as mock:
        mock.return_value = MagicMock(spec=Agent)
        yield mock


@pytest.fixture
def mock_crewai_task():
    """Create a mock crewai task."""
    with patch("local_newsifier.crews.investigation_crew.Task") as mock:
        mock.return_value = MagicMock(spec=Task)
        yield mock


@pytest.fixture
def mock_crewai_crew():
    """Create a mock crewai crew."""
    with patch("local_newsifier.crews.investigation_crew.Crew") as mock:
        mock.return_value = MagicMock(spec=Crew)
        mock.return_value.kickoff.return_value = "Investigation results"
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
    """Create a test instance of NewsInvestigationCrew."""
    with patch("local_newsifier.crews.investigation_crew.EntityResolver", return_value=mock_entity_resolver), \
         patch("local_newsifier.crews.investigation_crew.EntityTracker", return_value=mock_entity_tracker), \
         patch("local_newsifier.crews.investigation_crew.ContextAnalyzer", return_value=mock_context_analyzer), \
         patch("local_newsifier.crews.investigation_crew.FileWriter", return_value=mock_file_writer):
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
        mock_crewai_crew.assert_called_once()  # One crew should be created

    def test_investigate_with_topic(
        self, investigation_crew, mock_crewai_crew, mock_crewai_task, mock_entity_tracker
    ):
        """Test investigating with a provided topic."""
        # Mock entity tracker response
        mock_entity_tracker.get_entity_connections.return_value = [
            {
                "source_entity": "Entity A",
                "target_entity": "Entity B",
                "relationship_type": "connection",
                "confidence_score": 0.9,
                "source_article_ids": "1"  # String instead of list
            }
        ]
        
        # Perform investigation
        result = investigation_crew.investigate(initial_topic="Local real estate development")
        
        # Verify crew was used
        assert mock_crewai_crew.return_value.kickoff.called
        
        # Verify the return value
        assert isinstance(result, InvestigationResult)
        assert result.topic == "Local real estate development"
        assert len(result.connections) > 0
        assert len(result.key_findings) > 0
        assert isinstance(result.evidence_score, int)
        assert 1 <= result.evidence_score <= 10

    def test_investigate_without_topic(
        self, investigation_crew, mock_crewai_crew, mock_crewai_task, mock_entity_tracker
    ):
        """Test investigating without a provided topic."""
        # Mock entity tracker response
        mock_entity_tracker.get_entity_connections.return_value = [
            {
                "source_entity": "Entity A",
                "target_entity": "Entity B",
                "relationship_type": "connection",
                "confidence_score": 0.9,
                "source_article_ids": "1"  # String instead of list
            }
        ]
        
        # Perform investigation
        result = investigation_crew.investigate()
        
        # Verify crew was used
        assert mock_crewai_crew.return_value.kickoff.called
        
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
                {
                    "source_entity": "Entity A",
                    "target_entity": "Entity B",
                    "relationship_type": "connection",
                    "confidence_score": 0.9,
                    "source_article_ids": "1"  # String instead of list
                }
            ],
            entities_of_interest=["Entity A", "Entity B"]
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
                {
                    "source_entity": "Entity A",
                    "target_entity": "Entity B",
                    "relationship_type": "connection",
                    "confidence_score": 0.9,
                    "source_article_ids": "1"  # String instead of list
                }
            ],
            entities_of_interest=["Entity A", "Entity B"]
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
            entities_of_interest=[]
        )
        
        # Generate report without specifying path
        report_path = investigation_crew.generate_report(investigation)
        
        # Verify file writer was called with default path
        assert mock_file_writer.write_file.called
        expected_path = f"output/investigation_{investigation.topic.replace(' ', '_')}.md"
        assert mock_file_writer.write_file.call_args[0][0] == expected_path
        assert report_path == expected_path

    def test_extract_entities_from_connections(self, investigation_crew):
        """Test extracting unique entities from connections."""
        # Create test connections
        connections = [
            {
                "source_entity": "Entity A",
                "target_entity": "Entity B",
                "relationship_type": "type1",
                "confidence_score": 0.8,
                "source_article_ids": "1"  # String instead of list
            },
            {
                "source_entity": "Entity B",
                "target_entity": "Entity C",
                "relationship_type": "type2",
                "confidence_score": 0.7,
                "source_article_ids": "2"  # String instead of list
            },
            {
                "source_entity": "Entity A",
                "target_entity": "Entity C",
                "relationship_type": "type3",
                "confidence_score": 0.9,
                "source_article_ids": "3"  # String instead of list
            }
        ]
        
        # Extract entities
        entities = investigation_crew._extract_entities_from_connections(connections)
        
        # Verify result
        assert set(entities) == {"Entity A", "Entity B", "Entity C"}