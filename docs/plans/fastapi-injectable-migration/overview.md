# FastAPI-Injectable Migration Plan Overview

## Executive Summary

This document outlines the plan to migrate away from FastAPI-Injectable as part of our broader transition to:
1. Fully async architecture (see [convert_to_async.md](../convert_to_async.md))
2. CLI-to-HTTP migration (see [cli-to-fastapi-overview.md](../cli_to_http/cli-to-fastapi-overview.md))

The migration from FastAPI-Injectable is a natural consequence of these architectural changes and will simplify our dependency management while enabling better async support.

## Why Migrate Away from FastAPI-Injectable?

### 1. Event Loop Conflicts
- FastAPI-Injectable creates event loop management issues when used outside of FastAPI contexts
- The CLI's direct use of injectable dependencies causes async/sync conflicts
- Tests require complex event loop fixtures and workarounds

### 2. Architectural Misalignment
- With CLI moving to HTTP-based architecture, direct DI in CLI becomes unnecessary
- FastAPI's built-in `Depends()` is sufficient for HTTP endpoints
- The extra abstraction layer adds complexity without proportional benefits

### 3. Async Migration Impediments
- FastAPI-Injectable's caching mechanisms complicate async session management
- The framework wasn't designed with full async stack in mind
- Provider functions with `use_cache=False` everywhere indicate we're fighting the framework

### 4. Testing Complexity
- Current tests require elaborate mocking of injectable providers
- Event loop issues force us to skip tests in CI (`@ci_skip_async`)
- The testing overhead outweighs the DI benefits

## Target Architecture

### Before (Current State)
```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│   FastAPI   │────▶│ FastAPI-Injectable│────▶│  Services   │
│  Endpoints  │     │    @injectable    │     │   (Sync)    │
└─────────────┘     └──────────────────┘     └─────────────┘
                              │
┌─────────────┐               │
│     CLI     │───────────────┘
│  Commands   │  (Direct DI - causes issues)
└─────────────┘
```

### After (Target State)
```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│   FastAPI   │────▶│  FastAPI    │────▶│   Services   │
│  Endpoints  │     │  Depends()  │     │   (Async)    │
└─────────────┘     └─────────────┘     └──────────────┘

┌─────────────┐     ┌─────────────┐
│     CLI     │────▶│    HTTP     │
│  Commands   │     │   Client    │
└─────────────┘     └─────────────┘
```

## Migration Benefits

### 1. Simplified Dependency Management
- Use FastAPI's native `Depends()` directly
- No additional abstraction layer
- Clear, explicit dependencies in function signatures

### 2. Better Async Support
- Services can be fully async without DI framework constraints
- No caching concerns with async sessions
- Clean async/await patterns throughout

### 3. Cleaner Testing
- Standard FastAPI `TestClient` for API tests
- Simple mocking with `unittest.mock`
- No event loop fixture requirements

### 4. Reduced Complexity
- One less framework to maintain and understand
- Fewer abstraction layers
- More straightforward debugging

## Migration Phases

### Phase 1: Prepare Services (Aligned with Async Migration)
- Remove `@injectable` decorators from services
- Convert services to accept dependencies as constructor parameters
- Make services async-first

### Phase 2: Update FastAPI Endpoints
- Replace injectable providers with direct FastAPI dependencies
- Convert provider functions to standard FastAPI dependency functions
- Remove `@injectable` decorators and `use_cache` parameters

### Phase 3: Migrate CLI to HTTP (Aligned with CLI-to-HTTP Migration)
- Remove all direct DI usage from CLI
- Implement HTTP client for CLI-to-API communication
- Remove CLI-specific provider functions

### Phase 4: Clean Up
- Remove fastapi-injectable dependency from pyproject.toml
- Delete old provider functions
- Update documentation

## Key Principles

### 1. Incremental Migration
- Migrate alongside async and CLI-to-HTTP efforts
- Maintain backward compatibility during transition
- Test thoroughly at each phase

### 2. Explicit Dependencies
- Services receive dependencies via constructor
- No hidden magic or implicit resolution
- Type hints for all dependencies

### 3. Async-First Design
- All I/O-bound services become async
- Use `AsyncSession` for database operations
- Leverage async concurrency benefits

## Success Criteria

1. **No FastAPI-Injectable imports** remain in codebase
2. **All tests pass** without event loop fixtures
3. **Performance improves** due to async operations
4. **Code is simpler** with fewer abstraction layers
5. **Developer experience improves** with clearer dependency flow

## Timeline

This migration is tied to the broader async and CLI-to-HTTP migrations:
- **Weeks 1-2**: Service preparation (with async migration)
- **Week 3**: FastAPI endpoint updates
- **Week 4**: CLI migration completion
- **Week 5**: Cleanup and documentation

## Next Steps

See the following documents for detailed implementation plans:
- [Service Migration Guide](service-migration.md)
- [FastAPI Endpoint Migration](endpoint-migration.md)
- [CLI Migration Details](cli-migration.md)
- [Testing Strategy](testing-strategy.md)
