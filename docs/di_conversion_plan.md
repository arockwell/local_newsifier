# Dependency Injection Conversion Plan

**Status:** Completed

This document summarizes the plan that was used to complete the dependency injection (DI) conversion across the Local Newsifier codebase.

## Overview

All components now use the `fastapi-injectable` framework. Provider functions and injectable classes are in place across the codebase.

## Areas for Conversion (All Completed)

### 1. Flow Classes

Flow classes are central to the application's business logic and need to be fully integrated with the DI system.

| Class | Current Status | Tasks |
|-------|---------------|-------|
| `EntityTrackingFlow` | Completed | — |
| `NewsPipelineFlow` | Completed | — |
| `TrendAnalysisFlow` | Completed | — |
| `PublicOpinionFlow` | Completed | — |
| `RSSScrapingFlow` | Completed | — |

### 2. Tool Classes

Tool classes provide utilities used throughout the application and should be exposed via provider functions.

| Tool | Current Status | Tasks |
|------|---------------|-------|
| `RSSParser` | Completed | — |
| `WebScraper` | Completed | — |
| `SentimentAnalyzer` | Completed | — |
| `EntityExtractor` | Completed | — |
| `EntityResolver` | Completed | — |
| `FileWriter` | Completed | — |
| `TrendReporter` | Completed | — |

### 3. API Dependencies

API dependencies provide FastAPI integration points that need proper DI usage.

| API Component | Current Status | Tasks |
|--------------|---------------|-------|
| API Dependencies | Completed | — |
| API Routes | Completed | — |
| API Middleware | Completed | — |

### 4. Testing Infrastructure

Testing infrastructure needs to support easy mocking of provider functions and injectable classes.

| Component | Current Status | Tasks |
|-----------|---------------|-------|
| Test Fixtures | Completed | — |
| Mock Services | Completed | — |
| Test Isolation | Completed | — |

## Implementation Phases

### Phase 1: Complete Flow Classes Integration (completed)

1. Update each flow class to accept dependencies via constructor
2. Create provider functions for each flow
3. Update tests to use the provider functions
4. Ensure circular dependencies are handled properly

### Phase 2: Tool Registration and Usage (completed)

1. Create provider functions for all tools
2. Update code that directly instantiates tools to use injection
3. Implement appropriate fallbacks for direct usage
4. Add tests for provider-based tool usage

### Phase 3: Refine API Dependencies (completed)

1. Review API dependencies for consistent patterns
2. Implement request scoping for web requests
3. Update API tests to use dependency overrides

### Phase 4: Enhance Testing Infrastructure (completed)

1. Create standardized test fixtures for injectable usage
2. Implement helpers for service mocking in tests
3. Add mechanisms to reset providers between tests
4. Document testing patterns in dependency_injection.md

## Success Criteria

1. All services, flows, and tools have provider functions
2. Direct instantiation is eliminated in favor of dependency injection
3. Proper fallback patterns are implemented for graceful degradation
4. All tests pass with the new DI implementation
5. Documentation is updated to reflect the complete DI usage

## Important Implementation Notes

### Async Testing

When testing components with async code:

- Use `@pytest.mark.asyncio` for async tests
- Mock async dependencies with `AsyncMock`
- Avoid mixing sync and async patterns in tests

For detailed guidance on async testing patterns, see [Event Loop Stabilization](plans/event-loop-stabilization.md).

## Test Scenarios

1. CLI commands function correctly with injectable dependencies
2. API endpoints utilize dependencies from provider functions
3. Celery tasks operate with injected services
4. Circular dependencies are resolved properly
5. Service lifetimes are respected (singleton vs transient)
