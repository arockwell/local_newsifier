# FastAPI-Injectable Migration Plan

## Overview

This document outlines a comprehensive plan for migrating from our custom DI container to fastapi-injectable throughout the Local Newsifier project. It incorporates existing documentation with a prioritized implementation plan, testing strategy, and success criteria.

## Current Status

We have completed the migration to fastapi-injectable:

- The former adapter layer has been removed
- Core provider functions are defined for fundamental dependencies
- Documentation is complete with examples and best practices
- FastAPI integration is working with proper session management

## Migration Phases

### Phase 1: Foundation (Completed)

- ✅ Set up basic infrastructure
- ✅ Create provider functions for core dependencies
- ✅ Configure testing utilities
- ✅ Implement adapter layer for compatibility
- ✅ Update documentation
- ✅ Fix issues related to instance caching (use_cache=False/True)

### Phase 2: Gradual Migration (Completed)

The migration will proceed in a layered approach, moving from the data layer toward UI layers:

1. **CRUD Layer Migration**
   - Define provider functions for all CRUD components
   - Update test fixtures for CRUD components
   - Standardize access patterns for database sessions

2. **Services Layer Migration**
   - Convert key services to use `@injectable` pattern
   - Update service constructor signatures to use `Annotated[Type, Depends()]`
   - Develop and document best practices for service testing

3. **Tools Layer Migration**
   - Migrate analysis and extraction tools
   - Update entity tracking tools
   - Standardize tool initialization patterns

4. **Flows Layer Migration**
   - Convert entity tracking flow
   - Migrate pipeline flows
   - Ensure proper session handling in flows

### Phase 3: API Integration (Completed)

1. **API Dependencies**
   - Convert API dependency functions to use fastapi-injectable
   - Update request scoping for proper session management
   - Implement enhanced error handling

2. **API Endpoints**
   - Update endpoint definitions to use injected dependencies
   - Standardize response models and error handling
   - Optimize dependency chains for performance

### Phase 4: CLI Integration (Completed)

1. **Command Infrastructure**
   - Adapt CLI commands to use injected dependencies
   - Provide proper session management for CLI contexts
   - Ensure command isolation

2. **Integration Testing**
   - Update fixtures for CLI testing
   - Add integration tests for end-to-end flows

### Phase 5: Complete Migration (Completed)

1. **Cleanup**
   - Remove legacy DI container dependencies
   - Standardize all components on fastapi-injectable pattern
   - Deprecate and remove adapter layer

2. **Performance Optimization**
   - Review dependency chains for performance
   - Optimize caching strategies
   - Implement benchmarking for critical paths

## Implementation Priority

Based on the analysis of current issues and PRs, the following items are prioritized:

### High Priority

1. **Testing Infrastructure** (Issue #179)
   - Develop standardized testing approach for injectable components
   - Create reusable fixtures for dependency overrides
   - Document testing patterns to ensure consistency

2. **Caching Strategy Refinement** (Issue #183)
   - Review current string-based pattern matching for caching decisions
   - Implement more principled approach to determine caching behavior
   - Add monitoring to detect incorrect caching that could lead to bugs

3. **Clean Public API** (Issue #184)
   - Design a clean, stable public API for the DI system
   - Hide implementation details from consumers
   - Provide forward-compatible migration path

### Medium Priority

1. **Logging and Monitoring** (Issue #185)
   - Enhance logging to provide visibility into dependency resolution
   - Add metrics for dependency resolution performance
   - Implement detection of circular dependencies

2. **Session Management**
   - Standardize session handling across the application
   - Ensure proper cleanup of database resources
   - Prevent session leakage between requests

3. **Provider Functions**
   - Complete provider functions for all common dependencies
   - Document caching behavior and thread safety guarantees
   - Implement optimization for frequent dependencies

### Lower Priority

1. **Documentation**
   - Update all documentation to reflect fastapi-injectable patterns
   - Create examples for common use cases
   - Document migration patterns for custom components

2. **Error Handling**
   - Implement standardized error handling for dependency failures
   - Provide clear error messages for missing dependencies
   - Add graceful degradation for optional dependencies

## Testing Strategy

Testing is critical to ensure the migration doesn't introduce regressions. The strategy includes:

1. **Unit Testing**
   - Test individual components in isolation
   - Mock dependencies to control test boundaries
   - Verify component behavior with different dependency configurations

2. **Integration Testing**
   - Test interaction between components
   - Verify proper session management across component boundaries
   - Test end-to-end flows with real dependencies

3. **Performance Testing**
   - Benchmark key operations before and after migration
   - Identify performance bottlenecks in dependency resolution
   - Optimize critical paths

## Success Criteria

The migration will be considered successful when:

1. All components use fastapi-injectable for dependency resolution
2. No references to the old container remain in the codebase
3. All tests pass with the new dependency injection system
4. Performance matches or exceeds the previous implementation
5. Documentation is complete and up-to-date
6. Developers can easily understand and use the new pattern

## Risk Management

Potential risks and mitigation strategies:

1. **Session Management**
   - Risk: Improper session handling leading to connection pool exhaustion
   - Mitigation: Standardize session management patterns and add monitoring

2. **Performance Regression**
   - Risk: Dependency resolution becoming a performance bottleneck
   - Mitigation: Add performance monitoring and optimize critical paths

3. **Testing Coverage**
   - Risk: Inadequate testing leading to regressions
   - Mitigation: Increase test coverage and add specific tests for edge cases

4. **Developer Adoption**
   - Risk: Inconsistent adoption of new patterns
   - Mitigation: Clear documentation and examples for common use cases

## Timeline

The migration is expected to follow this timeline:

- Phase 2 (Gradual Migration): 4-6 weeks
- Phase 3 (API Integration): 2-3 weeks
- Phase 4 (CLI Integration): 2-3 weeks
- Phase 5 (Complete Migration): 2-4 weeks

Total expected timeline: 10-16 weeks

## Resources

- [FastAPI-Injectable Documentation](https://fastapi-injectable.readme.io/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Python Type Annotations](https://docs.python.org/3/library/typing.html)
