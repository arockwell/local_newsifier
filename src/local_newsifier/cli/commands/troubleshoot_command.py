"""
Troubleshoot Command for identifying patterns across related PRs and issues.

This module implements the /troubleshoot command functionality to help with
pattern-based debugging across related GitHub issues and PRs.
"""

import re
import json
import argparse
from typing import List, Dict, Any, Optional, Tuple
import subprocess
from collections import Counter


class TroubleshootCommand:
    """
    Command implementation for pattern-based debugging of issues across PRs and issues.
    """
    
    def __init__(self):
        """Initialize the troubleshoot command."""
        self.parser = self._create_parser()
        self.technical_areas = {
            "di": "dependency injection",
            "async": "asynchronous code and event loops",
            "testing": "testing frameworks and patterns", 
            "database": "database sessions and transactions"
        }
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for the command."""
        parser = argparse.ArgumentParser(
            description="Analyze patterns across PRs and issues to identify common problems"
        )
        parser.add_argument(
            "context_message", 
            nargs="*", 
            help="Brief description of the problem pattern"
        )
        parser.add_argument(
            "--issues", 
            nargs="+", 
            help="Space-separated GitHub issue numbers",
            default=[]
        )
        parser.add_argument(
            "--prs", 
            nargs="+", 
            help="Space-separated PR numbers with common failures",
            default=[]
        )
        parser.add_argument(
            "--area", 
            help="Technical area to focus analysis (e.g., di, async, testing, database)",
            default=""
        )
        return parser
    
    def parse_args(self, args: str) -> Tuple[argparse.Namespace, str]:
        """
        Parse command arguments.
        
        Args:
            args: Command arguments as a string
            
        Returns:
            Tuple of (parsed arguments, error message if any)
        """
        try:
            # Split the arguments string into parts
            args_parts = args.split()
            
            # Extract --issues, --prs, and --area
            parsed_args = self.parser.parse_args(args_parts)
            
            # Convert issue and PR numbers to integers
            if parsed_args.issues:
                parsed_args.issues = [int(issue) for issue in parsed_args.issues]
            if parsed_args.prs:
                parsed_args.prs = [int(pr) for pr in parsed_args.prs]
                
            # Check for required parameters
            if not parsed_args.issues and not parsed_args.prs:
                return parsed_args, "Error: You must specify at least one issue or PR number"
            
            return parsed_args, ""
        except Exception as e:
            return None, f"Error parsing arguments: {str(e)}"
    
    def run(self, args: str) -> str:
        """
        Run the troubleshoot command.
        
        Args:
            args: Command arguments as a string
            
        Returns:
            Command output as a string
        """
        # Parse arguments
        parsed_args, error = self.parse_args(args)
        if error:
            return error
        
        context_message = " ".join(parsed_args.context_message)
        issues = parsed_args.issues
        prs = parsed_args.prs
        area = parsed_args.area.lower() if parsed_args.area else ""
        
        # Validate technical area
        if area and area not in self.technical_areas:
            closest_area = self._find_closest_area(area)
            if closest_area:
                return f"Technical area '{area}' not recognized. Did you mean '{closest_area}'? Valid areas are: {', '.join(self.technical_areas.keys())}"
            else:
                return f"Technical area '{area}' not recognized. Valid areas are: {', '.join(self.technical_areas.keys())}"
        
        try:
            # Fetch GitHub data
            issues_data = self._fetch_issues(issues)
            prs_data = self._fetch_prs(prs)
            
            # If no data was fetched, return error
            if not issues_data and not prs_data:
                return "Error: Failed to fetch data for the specified issues and PRs"
            
            # Analyze patterns
            patterns = self._analyze_patterns(issues_data, prs_data, area)
            
            # Find documentation links
            doc_links = self._find_documentation(area, patterns)
            
            # Generate and return results
            return self._format_results(patterns, doc_links, context_message)
        
        except Exception as e:
            return f"Error executing troubleshoot command: {str(e)}"
    
    def _find_closest_area(self, area: str) -> Optional[str]:
        """
        Find the closest matching technical area.
        
        Args:
            area: User-provided technical area
            
        Returns:
            Closest matching area or None
        """
        # Simple algorithm to find the closest match
        for valid_area in self.technical_areas:
            if valid_area.startswith(area) or area in valid_area:
                return valid_area
        return None
    
    def _fetch_issues(self, issue_numbers: List[int]) -> List[Dict[str, Any]]:
        """
        Fetch issue data from GitHub API.
        
        Args:
            issue_numbers: List of issue IDs to fetch
            
        Returns:
            List of issue data dictionaries
        """
        issues_data = []
        
        for issue_id in issue_numbers:
            try:
                # Run gh CLI command to get issue data
                result = subprocess.run(
                    ["gh", "issue", "view", str(issue_id), "--json", "number,title,body,comments"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                issue_data = json.loads(result.stdout)
                issues_data.append(issue_data)
            except Exception as e:
                print(f"Warning: Failed to fetch issue #{issue_id}: {str(e)}")
        
        return issues_data
    
    def _fetch_prs(self, pr_numbers: List[int]) -> List[Dict[str, Any]]:
        """
        Fetch PR data from GitHub API.
        
        Args:
            pr_numbers: List of PR IDs to fetch
            
        Returns:
            List of PR data dictionaries
        """
        prs_data = []
        
        for pr_id in pr_numbers:
            try:
                # Run gh CLI command to get PR data
                result = subprocess.run(
                    ["gh", "pr", "view", str(pr_id), "--json", "number,title,body,files,checks"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                pr_data = json.loads(result.stdout)
                
                # Also fetch PR comments for error messages
                comment_result = subprocess.run(
                    ["gh", "pr", "view", str(pr_id), "--json", "comments"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                comments_data = json.loads(comment_result.stdout)
                pr_data["comments"] = comments_data.get("comments", [])
                
                prs_data.append(pr_data)
            except Exception as e:
                print(f"Warning: Failed to fetch PR #{pr_id}: {str(e)}")
        
        return prs_data
    
    def _analyze_patterns(self, issues_data: List[Dict[str, Any]], prs_data: List[Dict[str, Any]], area: str) -> Dict[str, Any]:
        """
        Analyze patterns across issues and PRs to identify common problems.
        
        Args:
            issues_data: List of issue data dictionaries
            prs_data: List of PR data dictionaries
            area: Technical area to focus analysis
            
        Returns:
            Dictionary of identified patterns
        """
        patterns = {
            "error_messages": self._extract_error_patterns(issues_data, prs_data),
            "file_paths": self._extract_file_patterns(issues_data, prs_data),
            "code_patterns": self._extract_code_patterns(issues_data, prs_data, area),
            "test_failures": self._extract_test_failures(prs_data),
        }
        
        # Add area-specific patterns
        if area:
            patterns["area_specific"] = self._extract_area_specific_patterns(issues_data, prs_data, area)
        
        return patterns
    
    def _extract_error_patterns(self, issues_data: List[Dict[str, Any]], prs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract common error messages from issues and PRs.
        
        Args:
            issues_data: List of issue data dictionaries
            prs_data: List of PR data dictionaries
            
        Returns:
            List of error patterns found
        """
        error_patterns = []
        
        # Common error message regex patterns
        error_regexes = [
            (r"RuntimeError: Event loop is closed", "Event loop closed"),
            (r"AssertionError: assert .* is not None", "None assertion failure"),
            (r"IntegrityError: .*", "Database integrity error"),
            (r"asyncio.exceptions.CancelledError", "Asyncio cancelled error"),
            (r"TypeError: Object of type .* is not JSON serializable", "JSON serialization error"),
            (r"RequestError: .*", "HTTP request error"),
            (r"ImportError: cannot import name .*", "Import error"),
            (r"NameError: name .* is not defined", "Name not defined error"),
            (r"AttributeError: .* has no attribute .*", "Attribute error"),
            (r"RuntimeError: Cannot use .* with .* loop", "Asyncio loop compatibility error"),
        ]
        
        all_texts = []
        
        # Extract text from issues
        for issue in issues_data:
            if issue.get("body"):
                all_texts.append(issue["body"])
            
            # Check issue comments
            for comment in issue.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
        
        # Extract text from PRs
        for pr in prs_data:
            if pr.get("body"):
                all_texts.append(pr["body"])
            
            # Check PR comments for error messages
            for comment in pr.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
            
            # Check checks/status for error messages
            for check in pr.get("checks", []):
                if check.get("output", {}).get("text"):
                    all_texts.append(check["output"]["text"])
        
        # Find all error matches using our patterns
        error_counts = {}
        
        for text in all_texts:
            for regex, name in error_regexes:
                matches = re.findall(regex, text)
                if matches:
                    if name not in error_counts:
                        error_counts[name] = {
                            "name": name,
                            "count": 0,
                            "examples": set()
                        }
                    
                    error_counts[name]["count"] += len(matches)
                    # Add up to 3 unique examples
                    for match in matches[:3]:
                        if len(error_counts[name]["examples"]) < 3:
                            error_counts[name]["examples"].add(match)
        
        # Convert to list and sort by frequency
        error_patterns = [
            {
                "name": data["name"],
                "count": data["count"],
                "examples": list(data["examples"])
            }
            for name, data in error_counts.items()
        ]
        
        error_patterns.sort(key=lambda x: x["count"], reverse=True)
        
        return error_patterns
    
    def _extract_file_patterns(self, issues_data: List[Dict[str, Any]], prs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract common file paths mentioned in issues and PRs.
        
        Args:
            issues_data: List of issue data dictionaries
            prs_data: List of PR data dictionaries
            
        Returns:
            List of file patterns found
        """
        file_patterns = []
        
        # Track files by frequency
        file_counts = {}
        
        # Look for files mentioned in PR changes
        for pr in prs_data:
            for file_entry in pr.get("files", []):
                filename = file_entry.get("path", "")
                if filename:
                    if filename not in file_counts:
                        file_counts[filename] = 0
                    file_counts[filename] += 1
        
        # Extract file paths from text (issues and PR descriptions)
        file_regex = r"(?:src|tests)/[\w/._-]+\.py"
        
        all_texts = []
        
        # Extract text from issues
        for issue in issues_data:
            if issue.get("body"):
                all_texts.append(issue["body"])
            
            # Check issue comments
            for comment in issue.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
        
        # Extract text from PRs
        for pr in prs_data:
            if pr.get("body"):
                all_texts.append(pr["body"])
            
            # Check PR comments for file paths
            for comment in pr.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
        
        # Find all file path matches
        for text in all_texts:
            matches = re.findall(file_regex, text)
            for filename in matches:
                if filename not in file_counts:
                    file_counts[filename] = 0
                file_counts[filename] += 1
        
        # Convert to list and sort by frequency
        file_patterns = [
            {
                "path": path,
                "count": count
            }
            for path, count in file_counts.items()
        ]
        
        file_patterns.sort(key=lambda x: x["count"], reverse=True)
        
        return file_patterns[:10]  # Return top 10 files
    
    def _extract_code_patterns(self, issues_data: List[Dict[str, Any]], prs_data: List[Dict[str, Any]], area: str) -> List[Dict[str, Any]]:
        """
        Extract common code patterns mentioned in issues and PRs.
        
        Args:
            issues_data: List of issue data dictionaries
            prs_data: List of PR data dictionaries
            area: Technical area to focus analysis
            
        Returns:
            List of code patterns found
        """
        # Define area-specific code patterns to look for
        area_patterns = {
            "di": [
                r"@injectable\(.+\)",
                r"Annotated\[.+, Depends\(.+\)\]",
                r"c\.get\(.+\)",
                r"container\.get\(.+\)"
            ],
            "async": [
                r"async def .+",
                r"await .+",
                r"asyncio\..+",
                r"run_until_complete\(.+\)"
            ],
            "testing": [
                r"@pytest\.fixture",
                r"@pytest\.mark\.parametrize",
                r"assert .+",
                r"mock\.patch\(.+\)"
            ],
            "database": [
                r"with session\.begin\(\):",
                r"session\.exec\(.+\)",
                r"session\.add\(.+\)",
                r"SQLModel\..+"
            ]
        }
        
        code_patterns = []
        pattern_counts = {}
        
        # Choose patterns based on area
        patterns_to_check = []
        if area and area in area_patterns:
            patterns_to_check = area_patterns[area]
        else:
            # Use all patterns if no specific area
            for area_specific_patterns in area_patterns.values():
                patterns_to_check.extend(area_specific_patterns)
        
        all_texts = []
        
        # Extract text from issues
        for issue in issues_data:
            if issue.get("body"):
                all_texts.append(issue["body"])
            
            # Check issue comments
            for comment in issue.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
        
        # Extract text from PRs
        for pr in prs_data:
            if pr.get("body"):
                all_texts.append(pr["body"])
            
            # Check PR comments for code patterns
            for comment in pr.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
        
        # Find all pattern matches
        for text in all_texts:
            for pattern in patterns_to_check:
                matches = re.findall(pattern, text)
                if matches:
                    if pattern not in pattern_counts:
                        pattern_counts[pattern] = {
                            "pattern": pattern,
                            "count": 0,
                            "examples": set()
                        }
                    
                    pattern_counts[pattern]["count"] += len(matches)
                    # Add up to 3 unique examples
                    for match in matches[:3]:
                        if len(pattern_counts[pattern]["examples"]) < 3:
                            pattern_counts[pattern]["examples"].add(match)
        
        # Convert to list and sort by frequency
        code_patterns = [
            {
                "pattern": data["pattern"],
                "count": data["count"],
                "examples": list(data["examples"])
            }
            for pattern, data in pattern_counts.items()
        ]
        
        code_patterns.sort(key=lambda x: x["count"], reverse=True)
        
        return code_patterns
    
    def _extract_test_failures(self, prs_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract common test failures from PRs.
        
        Args:
            prs_data: List of PR data dictionaries
            
        Returns:
            List of test failure patterns found
        """
        test_failures = []
        
        # Regex to identify test failures
        test_failure_regex = r"FAILED\s+([^:]+::\w+::\w+)"
        
        # Track test failures by frequency
        failure_counts = {}
        
        # Check PR comments and checks for test failures
        for pr in prs_data:
            all_texts = []
            
            # Add PR description
            if pr.get("body"):
                all_texts.append(pr["body"])
            
            # Add PR comments
            for comment in pr.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
            
            # Add check outputs
            for check in pr.get("checks", []):
                if check.get("output", {}).get("text"):
                    all_texts.append(check["output"]["text"])
            
            # Find all test failure matches
            for text in all_texts:
                matches = re.findall(test_failure_regex, text)
                for test_name in matches:
                    if test_name not in failure_counts:
                        failure_counts[test_name] = 0
                    failure_counts[test_name] += 1
        
        # Convert to list and sort by frequency
        test_failures = [
            {
                "test": test_name,
                "count": count
            }
            for test_name, count in failure_counts.items()
        ]
        
        test_failures.sort(key=lambda x: x["count"], reverse=True)
        
        return test_failures
    
    def _extract_area_specific_patterns(self, issues_data: List[Dict[str, Any]], prs_data: List[Dict[str, Any]], area: str) -> List[Dict[str, Any]]:
        """
        Extract patterns specific to a technical area.
        
        Args:
            issues_data: List of issue data dictionaries
            prs_data: List of PR data dictionaries
            area: Technical area to focus analysis
            
        Returns:
            List of area-specific patterns found
        """
        area_specific_patterns = []
        
        # Define area-specific keywords to look for
        area_keywords = {
            "di": ["dependency injection", "injectable", "provider", "container", "dependency", "circle"],
            "async": ["async", "await", "event loop", "coroutine", "future", "task", "asyncio"],
            "testing": ["pytest", "fixture", "mock", "assert", "parametrize", "patch"],
            "database": ["sqlmodel", "session", "transaction", "query", "commit", "rollback", "sql"]
        }
        
        # Choose keywords based on area
        keywords_to_check = []
        if area in area_keywords:
            keywords_to_check = area_keywords[area]
        else:
            # Try to find the closest match
            for key, words in area_keywords.items():
                if area in key or any(area in word for word in words):
                    keywords_to_check = words
                    break
        
        # If still no keywords, return empty list
        if not keywords_to_check:
            return area_specific_patterns
        
        # Track keyword mentions by frequency
        keyword_counts = {}
        
        all_texts = []
        
        # Extract text from issues
        for issue in issues_data:
            if issue.get("body"):
                all_texts.append(issue["body"])
            
            # Check issue comments
            for comment in issue.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
        
        # Extract text from PRs
        for pr in prs_data:
            if pr.get("body"):
                all_texts.append(pr["body"])
            
            # Check PR comments for keywords
            for comment in pr.get("comments", []):
                if comment.get("body"):
                    all_texts.append(comment["body"])
        
        # Find all keyword matches
        for text in all_texts:
            for keyword in keywords_to_check:
                # Case-insensitive search
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE))
                if count > 0:
                    if keyword not in keyword_counts:
                        keyword_counts[keyword] = 0
                    keyword_counts[keyword] += count
        
        # Convert to list and sort by frequency
        area_specific_patterns = [
            {
                "keyword": keyword,
                "count": count
            }
            for keyword, count in keyword_counts.items()
        ]
        
        area_specific_patterns.sort(key=lambda x: x["count"], reverse=True)
        
        return area_specific_patterns
    
    def _find_documentation(self, area: str, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find relevant documentation based on the specified area and patterns.
        
        Args:
            area: Technical area to focus analysis
            patterns: Dictionary of identified patterns
            
        Returns:
            List of relevant documentation links
        """
        # Define area to documentation mappings
        area_docs = {
            "di": [
                {"path": "docs/di_architecture.md", "description": "DI Architecture Guide"},
                {"path": "docs/injectable_patterns.md", "description": "Injectable Design Patterns"},
                {"path": "docs/dependency_injection.md", "description": "Dependency Injection Overview"},
                {"path": "docs/fastapi_injectable.md", "description": "FastAPI Injectable Integration"}
            ],
            "async": [
                {"path": "docs/testing_injectable_dependencies.md", "description": "Testing Async Dependencies"},
                {"path": "CLAUDE.md", "description": "Event Loop Issues in Tests"}
            ],
            "testing": [
                {"path": "docs/testing_guide.md", "description": "Testing Guide"},
                {"path": "docs/testing_injectable_dependencies.md", "description": "Testing Injectable Dependencies"},
                {"path": "tests/conftest.py", "description": "Test Fixtures"}
            ],
            "database": [
                {"path": "docs/db_diagnostics.md", "description": "Database Diagnostics"},
                {"path": "docs/db_initialization.md", "description": "Database Initialization"}
            ]
        }
        
        # Map specific error patterns to documentation
        error_docs = {
            "Event loop closed": [
                {"path": "CLAUDE.md", "section": "Handling Event Loop Issues in Tests", "description": "Event Loop Guidance"}
            ],
            "Asyncio loop compatibility error": [
                {"path": "docs/testing_injectable_dependencies.md", "description": "Async Testing Guide"},
                {"path": "CLAUDE.md", "section": "Handling Event Loop Issues in Tests", "description": "Event Loop Guidance"}
            ],
            "None assertion failure": [
                {"path": "docs/error_handling.md", "description": "Error Handling Guide"}
            ],
            "Database integrity error": [
                {"path": "docs/db_diagnostics.md", "description": "Database Diagnostics"}
            ]
        }
        
        relevant_docs = []
        
        # Add area-specific documentation
        if area and area in area_docs:
            relevant_docs.extend(area_docs[area])
        
        # Add documentation based on error patterns
        for error_pattern in patterns.get("error_messages", []):
            error_name = error_pattern.get("name")
            if error_name and error_name in error_docs:
                relevant_docs.extend(error_docs[error_name])
        
        # Add default docs if none found
        if not relevant_docs:
            relevant_docs = [
                {"path": "docs/error_handling.md", "description": "Error Handling Guide"},
                {"path": "CLAUDE.md", "description": "Project Documentation"}
            ]
        
        # Remove duplicates while preserving order
        unique_docs = []
        seen_paths = set()
        
        for doc in relevant_docs:
            if doc["path"] not in seen_paths:
                unique_docs.append(doc)
                seen_paths.add(doc["path"])
        
        return unique_docs
    
    def _format_results(self, patterns: Dict[str, Any], doc_links: List[Dict[str, Any]], context_message: str) -> str:
        """
        Format analysis results as a string.
        
        Args:
            patterns: Dictionary of identified patterns
            doc_links: List of relevant documentation links
            context_message: User-provided context message
            
        Returns:
            Formatted results string
        """
        result = []
        
        # Header
        result.append("# Troubleshooting Analysis Results\n")
        result.append(f"**Context:** {context_message}\n")
        
        # Error patterns
        result.append("## Common Error Patterns\n")
        
        if patterns["error_messages"]:
            result.append("| Error Type | Count | Examples |")
            result.append("|------------|-------|----------|")
            
            for error in patterns["error_messages"]:
                examples = error["examples"][0] if error["examples"] else "N/A"
                examples = examples[:50] + "..." if len(examples) > 50 else examples
                result.append(f"| {error['name']} | {error['count']} | {examples} |")
            
            result.append("")
        else:
            result.append("No common error patterns found.\n")
        
        # File paths
        result.append("## Most Frequently Referenced Files\n")
        
        if patterns["file_paths"]:
            result.append("| File Path | Count |")
            result.append("|-----------|-------|")
            
            for file in patterns["file_paths"][:5]:  # Show top 5
                result.append(f"| {file['path']} | {file['count']} |")
            
            result.append("")
        else:
            result.append("No common file references found.\n")
        
        # Test failures
        result.append("## Common Test Failures\n")
        
        if patterns["test_failures"]:
            result.append("| Test | Failure Count |")
            result.append("|------|---------------|")
            
            for test in patterns["test_failures"][:5]:  # Show top 5
                result.append(f"| {test['test']} | {test['count']} |")
            
            result.append("")
        else:
            result.append("No common test failures found.\n")
        
        # Relevant documentation
        result.append("## Relevant Documentation\n")
        
        if doc_links:
            result.append("| Path | Description |")
            result.append("|------|-------------|")
            
            for doc in doc_links:
                result.append(f"| {doc['path']} | {doc['description']} |")
            
            result.append("")
        else:
            result.append("No relevant documentation found.\n")
        
        # Root causes
        result.append("## Potential Root Causes\n")
        
        # Determine likely root causes based on patterns
        root_causes = []
        
        # Check for event loop issues
        if any("event loop" in error["name"].lower() for error in patterns["error_messages"]):
            root_causes.append(
                "Event loop issues in async tests - see CLAUDE.md:134 for guidance on using event_loop_fixture"
            )
        
        # Check for dependency injection issues
        if any("injectable" in pattern["pattern"] for pattern in patterns.get("code_patterns", [])):
            if any("async" in pattern["pattern"] for pattern in patterns.get("code_patterns", [])):
                root_causes.append(
                    "Async injectable dependencies - ensure proper use of event_loop_fixture in tests"
                )
            else:
                root_causes.append(
                    "Dependency injection configuration - check provider functions in di/providers.py"
                )
        
        # Check for database issues
        if any("database" in file["path"].lower() for file in patterns["file_paths"]):
            if any("integrity" in error["name"].lower() for error in patterns["error_messages"]):
                root_causes.append(
                    "Database integrity constraints - verify model relationships and cascade behavior"
                )
            else:
                root_causes.append(
                    "Database session management - ensure sessions are closed properly"
                )
        
        # Add default root cause if none identified
        if not root_causes:
            root_causes.append(
                "Insufficient information to determine root cause - please provide more error details"
            )
        
        for i, cause in enumerate(root_causes, 1):
            result.append(f"{i}. {cause}")
        
        result.append("")
        
        # Suggested solutions
        result.append("## Suggested Solutions\n")
        
        # Determine suggested solutions based on patterns
        solutions = []
        
        # Event loop solutions
        if any("event loop" in error["name"].lower() for error in patterns["error_messages"]):
            solutions.append(
                "Add event_loop_fixture to test functions that use async code: def test_function(event_loop_fixture):"
            )
            solutions.append(
                "Use event_loop_fixture.run_until_complete() for executing async code in tests"
            )
        
        # DI solutions
        if any("injectable" in pattern["pattern"] for pattern in patterns.get("code_patterns", [])):
            solutions.append(
                "Ensure injectable providers use use_cache=False for consistent behavior"
            )
            solutions.append(
                "Check for circular dependencies in provider functions"
            )
        
        # Database solutions
        if any("database" in file["path"].lower() for file in patterns["file_paths"]):
            solutions.append(
                "Use 'with session_factory() as session:' pattern to ensure sessions are closed"
            )
            solutions.append(
                "Verify cascade_delete settings on model relationships"
            )
        
        # Add default solution if none identified
        if not solutions:
            solutions.append(
                "Consult the documentation linked above for project patterns and best practices"
            )
        
        for i, solution in enumerate(solutions, 1):
            result.append(f"{i}. {solution}")
        
        return "\n".join(result)


# Command instance for direct usage
troubleshoot_cmd = TroubleshootCommand()


def process_command(args: str) -> str:
    """
    Process the troubleshoot command.
    
    Args:
        args: Command arguments as a string
        
    Returns:
        Command output as a string
    """
    return troubleshoot_cmd.run(args)