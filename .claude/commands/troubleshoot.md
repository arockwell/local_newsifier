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

I'll analyze patterns across GitHub issues and PRs to identify common problems based on the information in $ARGUMENTS. First, I'll parse the input to extract:

1. The context message describing the problem pattern
2. The issue numbers to investigate (from the --issues flag)
3. The PR numbers to analyze (from the --prs flag)
4. The technical area to focus on (from the --area flag, if provided)

## Troubleshooting Analysis Process

1. **Fetch GitHub Data**: I'll collect information from the specified issues and PRs:
   - For each issue number: titles, descriptions, comments, and associated metadata
   - For each PR number: descriptions, changed files, CI check outputs, and comments
   - I'll use the context message to guide my analysis focus

2. **Pattern Analysis**: I'll identify common patterns across these issues and PRs:
   - **Error Messages**: Extract recurring exceptions and error messages using regex
   - **File Paths**: Identify files that appear frequently in the problems
   - **Code Patterns**: Find potentially problematic code constructs 
   - **Test Failures**: Correlate specific test failures that appear across multiple PRs

3. **Technical Area Focus**: 
   If a technical area is specified in $ARGUMENTS, I'll focus my analysis on that domain:
   - **di**: Dependency injection issues, circular dependencies, provider configuration
   - **async**: Event loop problems, coroutine errors, asyncio misuse patterns
   - **testing**: Fixture issues, test isolation problems, mock configuration
   - **database**: Session handling, transaction issues, model definition problems

4. **Documentation Correlation**: I'll match identified patterns with relevant docs:
   - For dependency injection issues: docs/di_architecture.md, docs/injectable_patterns.md
   - For async/event loop issues: docs/testing_injectable_dependencies.md, CLAUDE.md
   - For testing issues: docs/testing_guide.md, tests/conftest.py
   - For database issues: docs/db_diagnostics.md, docs/db_initialization.md

5. **Root Cause Analysis**: Based on the patterns identified and context message from $ARGUMENTS, I'll determine the most likely underlying causes:
   - Check for event loop configuration issues in async tests
   - Look for dependency injection circular references or provider misconfigurations
   - Identify session management problems in database operations
   - Detect test isolation or fixture setup issues

## Output Format

I'll present my findings in a comprehensive report with these sections:

1. **Common Error Patterns**: Table of most frequent errors across the issues and PRs with counts and examples
2. **Frequently Referenced Files**: Files that appear most often in the problems
3. **Common Test Failures**: Tests that frequently fail in the analyzed PRs
4. **Relevant Documentation**: Links to documentation based on the patterns and technical area
5. **Potential Root Causes**: Analysis of likely underlying issues related to the context message
6. **Suggested Solutions**: Actionable steps to address the identified problems, with specific code examples where appropriate

For example, if event loop issues are detected in async tests, I'll recommend adding event_loop_fixture to test functions and provide specific code snippets showing correct usage.

My analysis will focus on providing practical, implementable solutions to address the common patterns found across the issues and PRs specified in $ARGUMENTS.