---
name: troubleshoot
description: Identify patterns across related PRs and issues with common problems
usage: |
  /troubleshoot <context_message> [--issues <issue_numbers>] [--prs <pr_numbers>] [--area <tech_area>]
arguments:
  - name: context_message
    description: Brief description of the problem pattern
    type: text
    required: true
  - name: issues
    description: Space-separated GitHub issue numbers
    type: text
    prefix: --issues
    required: false
  - name: prs
    description: Space-separated PR numbers with common failures
    type: text
    prefix: --prs
    required: false
  - name: area
    description: Technical area to focus analysis (e.g., di, async, testing, database)
    type: text
    prefix: --area
    required: false
---

I'll analyze patterns across GitHub issues and PRs to identify common problems matching "$context_message". Let me examine issues $issues and PRs $prs, focusing on the $area technical area if specified.

## Troubleshooting Analysis Process

1. **Fetch GitHub Data**: I'll collect information from the specified issues and PRs:
   - For issues $issues: titles, descriptions, comments, and associated metadata
   - For PRs $prs: descriptions, changed files, CI check outputs, and comments
   - Context will be focused on "$context_message" to guide my analysis

2. **Pattern Analysis**: I'll identify common patterns across these issues and PRs:
   - **Error Messages**: Extract recurring exceptions and error messages using regex
   - **File Paths**: Identify files that appear frequently in the problems
   - **Code Patterns**: Find potentially problematic code constructs 
   - **Test Failures**: Correlate specific test failures that appear across multiple PRs

3. **Technical Area Focus**: 
   If $area is specified, I'll focus my analysis on that domain:
   - **di**: Dependency injection issues, circular dependencies, provider configuration
   - **async**: Event loop problems, coroutine errors, asyncio misuse patterns
   - **testing**: Fixture issues, test isolation problems, mock configuration
   - **database**: Session handling, transaction issues, model definition problems

4. **Documentation Correlation**: I'll match identified patterns with relevant docs:
   - For dependency injection issues: docs/di_architecture.md, docs/injectable_patterns.md
   - For async/event loop issues: docs/testing_injectable_dependencies.md, CLAUDE.md
   - For testing issues: docs/testing_guide.md, tests/conftest.py
   - For database issues: docs/db_diagnostics.md, docs/db_initialization.md

5. **Root Cause Analysis**: Based on the patterns identified and "$context_message", I'll determine the most likely underlying causes:
   - Check for event loop configuration issues in async tests
   - Look for dependency injection circular references or provider misconfigurations
   - Identify session management problems in database operations
   - Detect test isolation or fixture setup issues

## Output Format

I'll present my findings in a comprehensive report with these sections:

1. **Common Error Patterns**: Table of most frequent errors across issues $issues and PRs $prs with counts and examples
2. **Frequently Referenced Files**: Files that appear most often in the problems
3. **Common Test Failures**: Tests that frequently fail in the analyzed PRs
4. **Relevant Documentation**: Links to documentation based on the patterns and $area
5. **Potential Root Causes**: Analysis of likely underlying issues related to "$context_message"
6. **Suggested Solutions**: Actionable steps to address the identified problems, with specific code examples where appropriate

For example, if event loop issues are detected in async tests, I'll recommend adding event_loop_fixture to test functions and provide specific code snippets showing correct usage.

My analysis will focus on providing practical, implementable solutions to address the common patterns found across issues $issues and PRs $prs.