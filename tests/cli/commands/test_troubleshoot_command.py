"""
Tests for the troubleshoot command implementation.

These tests verify that the troubleshoot command correctly parses arguments,
fetches GitHub data, analyzes patterns, and formats results.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from src.local_newsifier.cli.commands.troubleshoot_command import TroubleshootCommand, process_command


class TestTroubleshootCommand:
    """Test suite for the troubleshoot command."""
    
    @pytest.fixture
    def troubleshoot_cmd(self):
        """Return a troubleshoot command instance for testing."""
        return TroubleshootCommand()
    
    @pytest.fixture
    def mock_issue_data(self) -> List[Dict[str, Any]]:
        """Return mock issue data for testing."""
        return [{
            "number": 385,
            "title": "Fix event loop issues in tests",
            "body": "We're having RuntimeError: Event loop is closed errors in several tests.",
            "comments": [
                {
                    "body": "This happens in the WebScraperTool tests and when using async with injectable dependencies."
                }
            ]
        }]
    
    @pytest.fixture
    def mock_pr_data(self) -> List[Dict[str, Any]]:
        """Return mock PR data for testing."""
        return [{
            "number": 393,
            "title": "Fix for web scraper tests",
            "body": "This PR fixes the event loop issues in tests/tools/test_web_scraper.py",
            "files": [
                {"path": "tests/tools/test_web_scraper.py"},
                {"path": "src/local_newsifier/tools/web_scraper.py"}
            ],
            "checks": [
                {
                    "name": "pytest",
                    "status": "failure",
                    "output": {
                        "text": "FAILED tests/tools/test_web_scraper.py::TestWebScraper::test_fetch_content"
                    }
                }
            ],
            "comments": [
                {
                    "body": "This fails with RuntimeError: Cannot use run_until_complete with the running event loop"
                }
            ]
        }]
    
    def test_parse_args_with_valid_input(self, troubleshoot_cmd):
        """Test argument parsing with valid input."""
        args_str = "This is a test --issues 385 386 --prs 393 394 --area async"
        parsed_args, error = troubleshoot_cmd.parse_args(args_str)
        
        assert error == ""
        assert parsed_args is not None
        assert parsed_args.context_message == ["This", "is", "a", "test"]
        assert parsed_args.issues == [385, 386]
        assert parsed_args.prs == [393, 394]
        assert parsed_args.area == "async"
    
    def test_parse_args_with_missing_numbers(self, troubleshoot_cmd):
        """Test argument parsing with missing issue and PR numbers."""
        args_str = "This is a test --area async"
        parsed_args, error = troubleshoot_cmd.parse_args(args_str)
        
        assert "Error: You must specify at least one issue or PR number" in error
    
    def test_find_closest_area(self, troubleshoot_cmd):
        """Test finding the closest technical area match."""
        assert troubleshoot_cmd._find_closest_area("dep") == "di"
        assert troubleshoot_cmd._find_closest_area("asyncio") == "async"
        assert troubleshoot_cmd._find_closest_area("test") == "testing"
        assert troubleshoot_cmd._find_closest_area("db") == "database"
        assert troubleshoot_cmd._find_closest_area("nonexistent") is None
    
    @patch("subprocess.run")
    def test_fetch_issues(self, mock_run, troubleshoot_cmd, mock_issue_data):
        """Test fetching issues from GitHub API."""
        # Mock subprocess.run to return issue data
        mock_process = MagicMock()
        mock_process.stdout = json.dumps(mock_issue_data[0])
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        issues = troubleshoot_cmd._fetch_issues([385])
        
        # Verify subprocess.run was called with correct arguments
        mock_run.assert_called_once_with(
            ["gh", "issue", "view", "385", "--json", "number,title,body,comments"],
            capture_output=True,
            text=True,
            check=True
        )
        
        assert len(issues) == 1
        assert issues[0]["number"] == 385
    
    @patch("subprocess.run")
    def test_fetch_prs(self, mock_run, troubleshoot_cmd, mock_pr_data):
        """Test fetching PRs from GitHub API."""
        # Mock subprocess.run to return PR data
        mock_process_pr = MagicMock()
        mock_process_pr.stdout = json.dumps(mock_pr_data[0])
        mock_process_pr.returncode = 0
        
        mock_process_comments = MagicMock()
        mock_process_comments.stdout = json.dumps({"comments": mock_pr_data[0]["comments"]})
        mock_process_comments.returncode = 0
        
        mock_run.side_effect = [mock_process_pr, mock_process_comments]
        
        prs = troubleshoot_cmd._fetch_prs([393])
        
        # Verify subprocess.run was called with correct arguments
        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            ["gh", "pr", "view", "393", "--json", "number,title,body,files,checks"],
            capture_output=True,
            text=True,
            check=True
        )
        
        assert len(prs) == 1
        assert prs[0]["number"] == 393
    
    def test_extract_error_patterns(self, troubleshoot_cmd, mock_issue_data, mock_pr_data):
        """Test extracting error patterns from issues and PRs."""
        error_patterns = troubleshoot_cmd._extract_error_patterns(mock_issue_data, mock_pr_data)
        
        assert len(error_patterns) > 0
        # Verify the most common error pattern is related to event loop
        assert any("Event loop" in pattern["name"] for pattern in error_patterns)
    
    def test_extract_file_patterns(self, troubleshoot_cmd, mock_issue_data, mock_pr_data):
        """Test extracting file patterns from issues and PRs."""
        file_patterns = troubleshoot_cmd._extract_file_patterns(mock_issue_data, mock_pr_data)
        
        assert len(file_patterns) > 0
        # Verify web_scraper.py is in the file patterns
        assert any("web_scraper.py" in pattern["path"] for pattern in file_patterns)
    
    def test_extract_test_failures(self, troubleshoot_cmd, mock_pr_data):
        """Test extracting test failure patterns from PRs."""
        test_failures = troubleshoot_cmd._extract_test_failures(mock_pr_data)
        
        assert len(test_failures) > 0
        # Verify test_web_scraper.py is in the test failures
        assert any("test_web_scraper.py" in failure["test"] for failure in test_failures)
    
    def test_find_documentation(self, troubleshoot_cmd):
        """Test finding relevant documentation."""
        # Test with event loop error patterns
        patterns = {
            "error_messages": [
                {"name": "Event loop closed", "count": 3, "examples": ["RuntimeError: Event loop is closed"]}
            ],
            "file_paths": [
                {"path": "tests/tools/test_web_scraper.py", "count": 2}
            ]
        }
        
        docs = troubleshoot_cmd._find_documentation("async", patterns)
        
        assert len(docs) > 0
        # Verify CLAUDE.md is in the documentation
        assert any("CLAUDE.md" in doc["path"] for doc in docs)
    
    @patch.object(TroubleshootCommand, "_fetch_issues")
    @patch.object(TroubleshootCommand, "_fetch_prs")
    def test_run_command_full_integration(self, mock_fetch_prs, mock_fetch_issues, 
                                         troubleshoot_cmd, mock_issue_data, mock_pr_data):
        """Test the full command integration."""
        mock_fetch_issues.return_value = mock_issue_data
        mock_fetch_prs.return_value = mock_pr_data
        
        args_str = "Event loop test failure --issues 385 --prs 393 --area async"
        result = troubleshoot_cmd.run(args_str)
        
        # Verify the result contains key sections
        assert "# Troubleshooting Analysis Results" in result
        assert "## Common Error Patterns" in result
        assert "## Most Frequently Referenced Files" in result
        assert "## Common Test Failures" in result
        assert "## Relevant Documentation" in result
        assert "## Potential Root Causes" in result
        assert "## Suggested Solutions" in result
    
    @patch("src.local_newsifier.cli.commands.troubleshoot_command.troubleshoot_cmd")
    def test_process_command(self, mock_cmd):
        """Test the process_command function."""
        mock_cmd.run.return_value = "Test result"
        
        result = process_command("test args")
        
        mock_cmd.run.assert_called_once_with("test args")
        assert result == "Test result"