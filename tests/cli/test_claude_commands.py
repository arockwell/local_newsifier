"""Tests for the Claude CLI commands."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from local_newsifier.cli.commands.claude import (
    claude_group, analyze_sentiment, summarize_content, 
    extract_entities, generate_headline
)


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


class TestClaudeCommands:
    """Test the Claude CLI commands."""

    def test_analyze_sentiment(self, runner):
        """Test the analyze-sentiment command."""
        # Run the command
        result = runner.invoke(analyze_sentiment, ["This is a positive test text."])

        # Verify
        assert result.exit_code == 0
        assert "Sentiment Analysis Results:" in result.output
        assert "Text:" in result.output
        assert "Sentiment:" in result.output
        assert "Key emotions:" in result.output

    def test_analyze_sentiment_with_json_output(self, runner):
        """Test the analyze-sentiment command with JSON output."""
        # Run the command
        result = runner.invoke(analyze_sentiment, ["This is a test text.", "--json"])

        # Verify
        assert result.exit_code == 0
        
        # Parse the output as JSON to validate it
        output = json.loads(result.output)
        assert "text" in output
        assert "sentiment_score" in output
        assert "sentiment" in output
        assert "key_emotions" in output
        assert "confidence" in output

    def test_analyze_sentiment_with_output_file(self, runner):
        """Test the analyze-sentiment command with output to file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name

        try:
            # Run the command
            result = runner.invoke(
                analyze_sentiment, ["This is a test text.", "--output", output_file]
            )

            # Verify
            assert result.exit_code == 0
            assert f"Results written to {output_file}" in result.output

            # Check that the output file exists and has content
            with open(output_file, "r") as f:
                content = f.read()
                assert "Sentiment Analysis Results:" in content
                assert "Text:" in content
                assert "Sentiment:" in content
        finally:
            # Clean up
            os.unlink(output_file)

    def test_summarize_content(self, runner):
        """Test the summarize command."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("This is a test article about local news. " * 20)
            input_file = f.name

        try:
            # Run the command
            result = runner.invoke(summarize_content, [input_file])

            # Verify
            assert result.exit_code == 0
            assert "Summary Results:" in result.output
            assert "File:" in result.output
            assert "Summary:" in result.output
            assert "Key topics:" in result.output
        finally:
            # Clean up
            os.unlink(input_file)

    def test_summarize_content_with_length_option(self, runner):
        """Test the summarize command with length option."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("This is a test article about local news. " * 20)
            input_file = f.name

        try:
            # Run the command with length option
            result = runner.invoke(summarize_content, [input_file, "--length", "short"])

            # Verify
            assert result.exit_code == 0
            assert "Summary Results:" in result.output
            assert "This is a short summary" in result.output
        finally:
            # Clean up
            os.unlink(input_file)

    def test_summarize_content_with_json_output(self, runner):
        """Test the summarize command with JSON output."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("This is a test article about local news. " * 20)
            input_file = f.name

        try:
            # Run the command
            result = runner.invoke(summarize_content, [input_file, "--json"])

            # Verify
            assert result.exit_code == 0
            
            # Parse the output as JSON to validate it
            output = json.loads(result.output)
            assert "file" in output
            assert "length" in output
            assert "content_size" in output
            assert "summary" in output
            assert "key_topics" in output
        finally:
            # Clean up
            os.unlink(input_file)

    def test_extract_entities(self, runner):
        """Test the extract-entities command."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("John Smith from Gainesville Times reported about City Council's meeting on January 15, 2025.")
            input_file = f.name

        try:
            # Run the command
            result = runner.invoke(extract_entities, [input_file])

            # Verify
            assert result.exit_code == 0
            assert "Entity Extraction Results:" in result.output
            assert "File:" in result.output
            assert "Entity types:" in result.output
            assert "Total entities found:" in result.output
        finally:
            # Clean up
            os.unlink(input_file)

    def test_extract_entities_with_type_filter(self, runner):
        """Test the extract-entities command with type filtering."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("John Smith from Gainesville Times reported about City Council's meeting on January 15, 2025.")
            input_file = f.name

        try:
            # Run the command with type filter
            result = runner.invoke(extract_entities, [input_file, "--types", "person", "--types", "organization"])

            # Verify
            assert result.exit_code == 0
            assert "Entity Extraction Results:" in result.output
            assert "Entity types: person, organization" in result.output
        finally:
            # Clean up
            os.unlink(input_file)

    def test_extract_entities_with_min_confidence(self, runner):
        """Test the extract-entities command with minimum confidence filter."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("John Smith from Gainesville Times reported about City Council's meeting on January 15, 2025.")
            input_file = f.name

        try:
            # Run the command with min confidence
            result = runner.invoke(extract_entities, [input_file, "--min-confidence", "0.9"])

            # Verify
            assert result.exit_code == 0
            assert "Entity Extraction Results:" in result.output
            assert "Minimum confidence: 0.9" in result.output
        finally:
            # Clean up
            os.unlink(input_file)

    def test_generate_headline(self, runner):
        """Test the generate-headline command."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("The city council approved a new development plan for the downtown area yesterday. " * 5)
            input_file = f.name

        try:
            # Run the command
            result = runner.invoke(generate_headline, [input_file])

            # Verify
            assert result.exit_code == 0
            assert "Headline Generation Results:" in result.output
            assert "File:" in result.output
            assert "Style: informative" in result.output
            assert "Generated Headlines:" in result.output
        finally:
            # Clean up
            os.unlink(input_file)

    def test_generate_headline_with_style(self, runner):
        """Test the generate-headline command with style option."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("The city council approved a new development plan for the downtown area yesterday. " * 5)
            input_file = f.name

        try:
            # Run the command with style option
            result = runner.invoke(generate_headline, [input_file, "--style", "clickbait"])

            # Verify
            assert result.exit_code == 0
            assert "Headline Generation Results:" in result.output
            assert "Style: clickbait" in result.output
            assert "You Won't Believe" in result.output  # Common clickbait pattern
        finally:
            # Clean up
            os.unlink(input_file)

    def test_generate_headline_with_count(self, runner):
        """Test the generate-headline command with count option."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("The city council approved a new development plan for the downtown area yesterday. " * 5)
            input_file = f.name

        try:
            # Run the command with count option
            result = runner.invoke(generate_headline, [input_file, "--count", "2"])

            # Verify
            assert result.exit_code == 0
            assert "Headline Generation Results:" in result.output
            
            # Count the headline lines in the output (should be 2)
            headline_lines = [line for line in result.output.split("\n") if line.strip().startswith("1.") or line.strip().startswith("2.")]
            assert len(headline_lines) == 2
        finally:
            # Clean up
            os.unlink(input_file)

    def test_generate_headline_with_json_output(self, runner):
        """Test the generate-headline command with JSON output."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("The city council approved a new development plan for the downtown area yesterday. " * 5)
            input_file = f.name

        try:
            # Run the command with JSON output
            result = runner.invoke(generate_headline, [input_file, "--json"])

            # Verify
            assert result.exit_code == 0
            
            # Parse the output as JSON to validate it
            output = json.loads(result.output)
            assert "file" in output
            assert "content_size" in output
            assert "style" in output
            assert "headlines" in output
            assert "count" in output
            assert len(output["headlines"]) == output["count"]
        finally:
            # Clean up
            os.unlink(input_file)