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

To complete the `/troubleshoot` command, I'll analyze patterns across the specified GitHub issues and PRs to identify common problems and suggest solutions.

## Step 1: Fetch GitHub Data
I'll begin by fetching data for the specified issues and PRs using the GitHub API. For each PR and issue:
- I'll get titles, descriptions, and body content
- For PRs, I'll examine comments, CI check outputs, and file changes
- For issues, I'll check all comments and associated metadata

## Step 2: Extract Common Patterns
I'll analyze the content to identify patterns in:
- **Error messages**: extracting common exceptions and errors using regex
- **File paths**: finding files that appear frequently in problems
- **Code patterns**: identifying problematic code constructs
- **Test failures**: correlating specific test failures across PRs

## Step 3: Technical Area Analysis
If an area was specified (di, async, testing, database), I'll focus my analysis on that domain:
- **di**: dependency injection configuration, circular dependencies, provider issues
- **async**: event loop problems, coroutine errors, asyncio misuse
- **testing**: fixture issues, test isolation problems, mock setup
- **database**: session handling, transaction issues, model definitions

## Step 4: Documentation Correlation
I'll map identified patterns to relevant documentation:
- **Dependency Injection**: di_architecture.md, injectable_patterns.md
- **Async/Event Loops**: testing_injectable_dependencies.md, CLAUDE.md
- **Testing**: testing_guide.md, testing fixtures
- **Database**: db_diagnostics.md, db_initialization.md

## Step 5: Generate Comprehensive Analysis
I'll present my findings in a structured format:
1. Common error patterns with frequency and examples
2. Frequently referenced files 
3. Common test failures
4. Relevant documentation links
5. Potential root causes
6. Suggested solutions with specific, actionable steps

I'll ensure all recommendations are specific, detailed, and directly address the patterns identified in the analysis.