# CLI to FastAPI Migration Overview

## Summary

This plan outlines a complete migration strategy to convert the Local Newsifier CLI from using direct dependency injection (fastapi-injectable) to using FastAPI HTTP endpoints as the backend. This approach eliminates event loop conflicts and simplifies the architecture.

## Key Benefits

1. **No Event Loop Conflicts**: FastAPI handles all async complexity
2. **Simplified Testing**: Standard TestClient, no special fixtures needed
3. **Better Architecture**: Clear separation between CLI and API
4. **Future Flexibility**: Can add web UI, remote access, multiple instances
5. **Improved Debugging**: All operations go through HTTP, easy to trace
6. **Scalability**: Can run CLI from anywhere, supports distributed deployment

## Architecture Change

### Before
```
┌─────────┐     ┌────────────────┐     ┌──────────┐
│   CLI   │────▶│ Injectable DI  │────▶│ Database │
└─────────┘     └────────────────┘     └──────────┘
                         │
┌─────────┐     ┌────────┼────────┐
│FastAPI  │────▶│ Injectable DI  │
└─────────┘     └────────────────┘
```

### After
```
┌─────────┐     ┌─────────┐     ┌────────────────┐     ┌──────────┐
│   CLI   │────▶│  HTTP   │────▶│    FastAPI     │────▶│ Database │
└─────────┘     └─────────┘     └────────────────┘     └──────────┘
```

## Migration Phases

1. **Phase 1**: Create CLI Router (Week 1)
   - Design and implement FastAPI endpoints for CLI operations
   - Add request/response models
   - Implement background task support

2. **Phase 2**: Create CLI HTTP Client (Week 1)
   - Build HTTP client with sync and async methods
   - Implement error handling
   - Add local mode support for testing

3. **Phase 3**: Update Services (Week 2)
   - Remove @injectable decorators
   - Update methods to accept session parameters
   - Add async wrappers where needed

4. **Phase 4**: Update Tests (Week 2)
   - Migrate to TestClient
   - Remove event loop fixtures
   - Simplify test structure

5. **Phase 5**: Deployment (Week 3)
   - Update deployment configuration
   - Add rollback support
   - Document new setup

## Success Criteria

- All CLI commands work through HTTP API
- No event loop conflicts in tests
- Improved test execution speed
- Simplified deployment process
- Backward compatibility during migration
