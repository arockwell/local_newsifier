# /troubleshoot Command Documentation

## Overview

The `/troubleshoot` command helps identify patterns across related PRs and issues that share common underlying problems. This command is especially useful when multiple PRs are encountering similar failures or when issues persist despite multiple fix attempts.

## Command Syntax

```
/troubleshoot <context_message>
    [--issues <issue_numbers>]
    [--prs <pr_numbers>]
    [--area <tech_area>]
```

### Parameters

- `context_message`: Brief description of the problem pattern
- `--issues`: Space-separated GitHub issue numbers
- `--prs`: Space-separated PR numbers with common failures
- `--area`: Technical area to focus analysis (e.g., di, async, testing, database)

## Example Usage

```
/troubleshoot These PRs are all failing with similar errors but I can't figure out why. --issues 385 386 --prs 393 394 396 --area dependency-injection
```

## Functionality

When invoked, the `/troubleshoot` command:

1. Fetches the relevant issues and PRs via the GitHub API
2. Analyzes the content for common patterns in:
   - Error messages
   - File paths
   - Code patterns
   - Test failures
3. Correlates findings with documentation in the specified technical area
4. Presents findings with:
   - Common error identification
   - Potential root causes
   - Documentation links
   - Suggested solutions

## Technical Areas

The `--area` parameter accepts several technical areas for focused analysis:

- `di`: Dependency injection issues
- `async`: Asynchronous code and event loops
- `testing`: Testing frameworks and patterns
- `database`: Database sessions and transactions

## Documentation Correlation

For each technical area, the command correlates findings with relevant documentation:

- **Dependency Injection**:
  - `docs/di_architecture.md`
  - `docs/injectable_patterns.md`
  - `docs/fastapi_injectable.md`

- **Async/Event Loops**:
  - `docs/testing_injectable_dependencies.md`
  - `CLAUDE.md` (Event Loop Issues section)

- **Testing**:
  - `docs/testing_guide.md`
  - `docs/testing_injectable_dependencies.md`

- **Database**:
  - `docs/db_diagnostics.md`
  - `docs/db_initialization.md`

## Output Format

The command output is structured into sections:

1. **Common Error Patterns**: Most frequent errors found across issues/PRs
2. **Frequently Referenced Files**: Files that appear most often in issues/PRs
3. **Common Test Failures**: Tests that frequently fail in the analyzed PRs
4. **Relevant Documentation**: Links to documentation based on identified patterns
5. **Potential Root Causes**: Analysis of likely underlying issues
6. **Suggested Solutions**: Actionable steps to address the identified problems

## Common Use Cases

- Test failures appearing only in CI but passing locally
- Multiple PRs encountering the same error pattern
- Issues that have persisted despite multiple fix attempts
- Complex integration problems spanning multiple components

## Implementation Details

### GitHub Data Fetching

The command uses the GitHub API to fetch:
- Issue titles, descriptions, and comments
- PR descriptions, files changed, and build logs
- CI check outputs and failure messages

### Pattern Analysis

Pattern analysis includes:
- Regex-based error message extraction
- Common file path identification
- Code pattern recognition
- Test failure correlation

### Algorithm

1. Extract text content from issues and PRs
2. Apply area-specific regex patterns to identify common issues
3. Count occurrences of patterns to identify most common problems
4. Map identified patterns to documentation and known solutions
5. Generate a comprehensive report for the user

## Example Output

```
=== Troubleshooting Analysis Results ===
Context: These PRs are all failing with similar errors but I can't figure out why

Common Error Patterns:
| Error Type                      | Count | Examples                                 |
|---------------------------------|-------|------------------------------------------|
| Event loop closed               | 5     | RuntimeError: Event loop is closed       |
| Asyncio loop compatibility error| 3     | RuntimeError: Cannot use run_until_... |

Most Frequently Referenced Files:
| File Path                                            | Count |
|------------------------------------------------------|-------|
| tests/flows/test_rss_scraping_flow.py                | 4     |
| tests/services/test_apify_service_schedules.py       | 3     |
| src/local_newsifier/tools/web_scraper.py             | 2     |

Common Test Failures:
| Test                                               | Failure Count |
|----------------------------------------------------|---------------|
| tests/flows/test_rss_scraping_flow.py::test_process| 3             |
| tests/services/test_apify_service::test_schedule   | 2             |

Relevant Documentation:
| Path                                  | Description                |
|---------------------------------------|----------------------------|
| CLAUDE.md                             | Event Loop Issues in Tests |
| docs/testing_injectable_dependencies.md | Testing Async Dependencies |

Potential Root Causes:
1. Event loop issues in async tests - see CLAUDE.md:134 for guidance on using event_loop_fixture
2. Async injectable dependencies - ensure proper use of event_loop_fixture in tests

Suggested Solutions:
1. Add event_loop_fixture to test functions that use async code: def test_function(event_loop_fixture):
2. Use event_loop_fixture.run_until_complete() for executing async code in tests
3. Ensure injectable providers use use_cache=False for consistent behavior
```