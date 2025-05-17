# Dependency Injection Conversion Plan

This document summarizes the plan that was used to complete the dependency injection (DI) conversion across the Local Newsifier codebase.

## Overview

All components now use the `fastapi-injectable` framework. Provider functions and injectable classes are in place across the codebase.

## Areas for Conversion

### 1. Flow Classes

Flow classes are central to the application's business logic and need to be fully integrated with the DI system.

| Class | Current Status | Tasks |
|-------|---------------|-------|
| `EntityTrackingFlow` | Basic integration | - Update constructor to accept dependencies<br>- Add provider function<br>- Update tests |
| `NewsPipelineFlow` | Basic integration | - Update constructor to accept dependencies<br>- Add provider function<br>- Update tests |
| `TrendAnalysisFlow` | Not integrated | - Update constructor to accept dependencies<br>- Add provider function<br>- Update tests |
| `PublicOpinionFlow` | Not integrated | - Update constructor to accept dependencies<br>- Add provider function<br>- Update tests |
| `RSSScrapingFlow` | Partial integration | - Complete constructor parameters<br>- Update tests |

### 2. Tool Classes

Tool classes provide utilities used throughout the application and should be exposed via provider functions.

| Tool | Current Status | Tasks |
|------|---------------|-------|
| `RSSParser` | Registered | - Update instantiation to use provider functions |
| `WebScraper` | Registered | - Update instantiation to use provider functions |
| `SentimentAnalyzer` | Not registered | - Add provider function<br>- Update usages |
| `EntityExtractor` | Not registered | - Add provider function<br>- Update usages |
| `EntityResolver` | Not registered | - Add provider function<br>- Update usages |
| `FileWriter` | Not registered | - Add provider function<br>- Update usages |
| `TrendReporter` | Not registered | - Add provider function<br>- Update usages |

### 3. API Dependencies

API dependencies provide FastAPI integration points that need proper DI usage.

| API Component | Current Status | Tasks |
|--------------|---------------|-------|
| API Dependencies | Basic integration | - Review all dependencies<br>- Ensure consistent patterns<br>- Add missing dependencies |
| API Routes | Varied integration | - Ensure all routes use dependencies<br>- Review manual instantiation |
| API Middleware | Not integrated | - Implement request scoping |

### 4. Testing Infrastructure

Testing infrastructure needs to support easy mocking of provider functions and injectable classes.

| Component | Current Status | Tasks |
|-----------|---------------|-------|
| Test Fixtures | Basic fixtures | - Create injectable fixtures<br>- Add service mocking helpers |
| Mock Services | Manual mocking | - Standardize service mocking pattern |
| Test Isolation | Manual setup | - Implement dependency overrides<br>- Reset providers between tests |

## Implementation Phases

### Phase 1: Complete Flow Classes Integration

1. Update each flow class to accept dependencies via constructor
2. Create provider functions for each flow
3. Update tests to use the provider functions
4. Ensure circular dependencies are handled properly

### Phase 2: Tool Registration and Usage

1. Create provider functions for all tools
2. Update code that directly instantiates tools to use injection
3. Implement appropriate fallbacks for direct usage
4. Add tests for provider-based tool usage

### Phase 3: Refine API Dependencies

1. Review API dependencies for consistent patterns
2. Implement request scoping for web requests
3. Update API tests to use dependency overrides

### Phase 4: Enhance Testing Infrastructure

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

### Event Loop Handling

Components using the `@injectable` decorator may encounter event loop issues in tests. To avoid these problems:

- Use the [conditional decorator pattern](injectable_patterns.md#the-conditional-decorator-pattern) when implementing components
- Add the `event_loop_fixture` to all tests that interact with injectable components
- Consider using `ci_skip_injectable` for tests that cannot avoid event loop issues in CI environments

For detailed guidance, see the [Event Loop Handling in Tests](injectable_patterns.md#event-loop-handling-in-tests) section in the Injectable Patterns Guide.

## Test Scenarios

1. CLI commands function correctly with injectable dependencies
2. API endpoints utilize dependencies from provider functions
3. Celery tasks operate with injected services
4. Circular dependencies are resolved properly
5. Service lifetimes are respected (singleton vs transient)
