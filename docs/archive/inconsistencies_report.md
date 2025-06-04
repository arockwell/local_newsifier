# Documentation Inconsistencies Report

## Critical Issues

### 1. Dependency Injection Documentation (HIGHEST PRIORITY)
**Files affected**:
- `guides/dependency_injection.md`
- `guides/testing_injectable_dependencies.md`
- `CLAUDE.md`

**Issue**: Documentation states both API and CLI use fastapi-injectable, but API has migrated to native FastAPI DI.

**Current Reality**:
- API: Uses native FastAPI dependency injection (see `src/local_newsifier/api/dependencies.py`)
- CLI: Still uses fastapi-injectable (see `src/local_newsifier/di/providers.py`)

**Fix needed**: Update all DI docs to clearly explain the hybrid approach.

### 2. Completed Migrations Still Documented
**Files affected**:
- `plans/async-to-sync-migration.md`
- `plans/async-to-sync-webhook-migration.md`

**Issue**: These migrations are complete but plans remain, confusing readers about current state.

**Evidence**:
- All webhook handlers are synchronous (see `src/local_newsifier/api/routers/webhooks.py:49`)
- No async/await patterns in codebase

### 3. Duplicate CLI Migration Plans
**Files with duplicate content**:
- `plans/cli-commands-refactoring.md`
- `plans/cli_to_http/cli-commands-refactoring.md`
- `plans/cli-http-client-design.md`
- `plans/cli_to_http/cli-http-client-design.md`

**Issue**: Same content in multiple locations, unclear which is authoritative.

### 4. Testing Documentation Inconsistencies
**Files affected**:
- `guides/testing_guide.md`
- `guides/testing_injectable_dependencies.md`

**Issue**: Mix examples for both DI systems without clear guidance on when to use which.

**Example conflict**:
- testing_guide.md shows native FastAPI testing
- testing_injectable_dependencies.md shows injectable patterns
- No clear statement that API uses one, CLI uses other

### 5. Dead References in Main Docs
**File**: `docs/README.md`

**Issues**:
- Links to archived gameplan files as if current
- References to "see the archive" without explaining it's historical
- No clear distinction between current and archived docs

### 6. Offline Installation Documentation
**Files affected**:
- `guides/offline_installation.md`
- `guides/offline_installation_troubleshooting.md`
- Multiple archive files about offline installation

**Issue**: Current status unclear - are offline installations still supported? Wheels directory exists but docs don't clarify.

### 7. Database Documentation Confusion
**Files affected**:
- `operations/db_diagnostics.md`
- `operations/db_initialization.md`

**Issue**:
- Cursor-specific database setup mentioned in some places but not others
- Alembic migrations mentioned but unclear if they're used
- Multiple database initialization approaches documented

### 8. Integration Documentation
**Apify docs scattered**:
- `integrations/apify/integration.md`
- `integrations/apify/error_handling.md`
- `integrations/apify/webhook_testing.md`
- `plans/apify-integration.md`

**Issue**: Information spread across 4 files with overlap and some contradictions about webhook handling.

### 9. Enhancement Roadmap
**File**: `plans/enhancement-roadmap.md`

**Issue**: Contains future plans from months ago - unclear what's been implemented vs. what's still planned.

### 10. Service Layer Documentation
**File**: `plans/service-layer-migration.md`

**Issue**: Describes a migration but unclear if complete. Code shows services exist but migration status unknown.

## Summary Statistics
- **Outdated files**: 15+ files
- **Duplicate content**: 8 file pairs
- **Dead references**: 10+ broken links
- **Inconsistent information**: 20+ conflicts between docs
- **Completed work still planned**: 5+ migrations

## Recommendation
1. **Immediate**: Fix DI documentation to prevent developer confusion
2. **Short-term**: Remove completed migration plans
3. **Medium-term**: Consolidate duplicate documentation
4. **Long-term**: Implement the gameplan.md strategy for overall reduction
