# Dependency Injection Conversion Plan

This document outlines the plan for completing the dependency injection (DI) conversion across the Local Newsifier codebase.

## Overview

We've already implemented a robust DI container with service lifecycle management, circular dependency resolution, and parameterized factories. The next phase involves expanding DI usage throughout the remaining components of the application.

## Areas for Conversion

### 1. Flow Classes

Flow classes are central to the application's business logic and need to be fully integrated with the DI system.

| Class | Current Status | Tasks |
|-------|---------------|-------|
| `EntityTrackingFlow` | Basic integration | - Update constructor to accept dependencies<br>- Register in container with factory<br>- Update tests |
| `NewsPipelineFlow` | Basic integration | - Update constructor to accept dependencies<br>- Register in container with factory<br>- Update tests |
| `TrendAnalysisFlow` | Not integrated | - Update constructor to accept dependencies<br>- Register in container with factory<br>- Update tests |
| `PublicOpinionFlow` | Not integrated | - Update constructor to accept dependencies<br>- Register in container with factory<br>- Update tests |
| `RSSScrapingFlow` | Partial integration | - Complete constructor parameters<br>- Update tests |

### 2. Tool Classes

Tool classes provide utilities used throughout the application and should be properly registered in the container.

| Tool | Current Status | Tasks |
|------|---------------|-------|
| `RSSParser` | Registered | - Update instantiation to use container |
| `WebScraper` | Registered | - Update instantiation to use container |
| `SentimentAnalyzer` | Not registered | - Add container registration<br>- Update usages |
| `EntityExtractor` | Not registered | - Add container registration<br>- Update usages |
| `EntityResolver` | Not registered | - Add container registration<br>- Update usages |
| `FileWriter` | Not registered | - Add container registration<br>- Update usages |
| `TrendReporter` | Not registered | - Add container registration<br>- Update usages |

### 3. API Dependencies

API dependencies provide FastAPI integration points that need proper DI usage.

| API Component | Current Status | Tasks |
|--------------|---------------|-------|
| API Dependencies | Basic integration | - Review all dependencies<br>- Ensure consistent patterns<br>- Add missing dependencies |
| API Routes | Varied integration | - Ensure all routes use dependencies<br>- Review manual instantiation |
| API Middleware | Not integrated | - Implement request scoping<br>- Consider child containers |

### 4. Testing Infrastructure

Testing infrastructure needs to support easy mocking and container configuration.

| Component | Current Status | Tasks |
|-----------|---------------|-------|
| Test Fixtures | Basic fixtures | - Create container fixture<br>- Add service mocking helpers |
| Mock Services | Manual mocking | - Standardize service mocking pattern<br>- Add container test helpers |
| Test Isolation | Manual setup | - Implement container snapshots<br>- Reset container between tests |

## Implementation Phases

### Phase 1: Complete Flow Classes Integration

1. Update each flow class to accept dependencies via constructor
2. Register flow classes in container.py with appropriate factories
3. Update tests to use container for flow class instantiation
4. Ensure circular dependencies are handled properly

### Phase 2: Tool Registration and Usage

1. Create complete tool registrations in container.py
2. Update code that directly instantiates tools to use container
3. Implement appropriate fallbacks for direct usage
4. Add tests for container-based tool usage

### Phase 3: Refine API Dependencies

1. Review API dependencies for consistent patterns
2. Implement request scoping for web requests
3. Consider child containers for request isolation
4. Update API tests to use container properly

### Phase 4: Enhance Testing Infrastructure

1. Create standardized test fixtures for container usage
2. Implement helpers for service mocking in tests
3. Add container reset mechanisms for test isolation
4. Document testing patterns in dependency_injection.md

## Success Criteria

1. All services, flows, and tools are registered in the container
2. Direct instantiation is eliminated in favor of container.get()
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

1. CLI commands function correctly with container dependencies
2. API endpoints utilize dependencies from the container
3. Celery tasks operate with container-provided services
4. Circular dependencies are resolved properly
5. Service lifetimes are respected (singleton vs transient)
