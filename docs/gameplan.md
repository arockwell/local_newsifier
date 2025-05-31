# Documentation Reduction Gameplan

## Overview
This plan outlines steps to reduce documentation volume by ~70% while improving accuracy and maintainability.

## Current State
- **Total docs**: 35 files (excluding archive)
- **Major issues**: Outdated DI docs, duplicate content, completed migration plans still present
- **Target**: Reduce to ~10-12 essential docs

## Phase 1: Immediate Removals (Day 1) ✅ COMPLETE
Remove completed/obsolete migration plans:
- [x] `plans/async-to-sync-migration.md` - Migration is complete
- [x] `plans/async-to-sync-webhook-migration.md` - Migration is complete
- [x] `plans/remove-celery.md` - If Celery removal is done
- [x] `plans/cli-to-fastapi-overview.md` - Outdated approach
- [x] `plans/deployment-configuration.md` - Duplicate of Railway config
- [x] `plans/table_creation_analysis.md` - One-time analysis

## Phase 2: Consolidation (Day 2-3)

### 1. Merge CLI Documentation
Combine into single `guides/cli_guide.md`:
- `plans/cli-commands-refactoring.md`
- `plans/cli-http-client-design.md`
- `plans/cli-router-implementation.md`
- All files in `plans/cli_to_http/`

### 2. Merge Testing Documentation
Combine into single `guides/testing_guide.md`:
- `guides/testing_guide.md` (update)
- `guides/testing_injectable_dependencies.md`
- `integrations/apify/webhook_testing.md`
- `plans/testing-strategy.md`

### 3. Merge Dependency Injection Docs
Create single accurate `guides/dependency_injection.md`:
- Current hybrid state (API uses native FastAPI, CLI uses injectable)
- Remove `guides/dependency_injection_antipatterns.md`
- Remove `guides/injectable_examples.md`
- Archive all fastapi-injectable migration plans

### 4. Merge Apify Documentation
Combine into `integrations/apify.md`:
- `integrations/apify/integration.md`
- `integrations/apify/error_handling.md`
- `integrations/apify/webhook_testing.md`
- `plans/apify-integration.md`

## Phase 3: Restructure (Day 4)

### Final Structure
```
docs/
├── README.md (simplified index)
├── guides/
│   ├── getting_started.md (combine setup guides)
│   ├── dependency_injection.md (accurate hybrid state)
│   ├── testing.md (all testing info)
│   ├── cli_usage.md (how to use CLI)
│   └── error_handling.md (keep as-is)
├── integrations/
│   ├── apify.md (all Apify docs)
│   └── celery.md (if still used)
├── operations/
│   ├── deployment.md (Railway + CI/CD)
│   └── database.md (combine db docs)
└── architecture/
    └── overview.md (high-level design)
```

## Phase 4: Update Root Docs (Day 5)

### 1. Update CLAUDE.md
- Remove references to archived/deleted docs
- Update DI section to reflect hybrid state
- Simplify to essential instructions only

### 2. Update README Files
- Main README.md: Focus on project overview
- docs/README.md: Simple index of available docs
- Remove duplicate setup instructions

## Success Metrics
- [ ] Documentation reduced from 35 to ~12 files
- [ ] All remaining docs accurate to current code
- [ ] No duplicate information
- [ ] Clear navigation structure
- [ ] All code examples tested and working

## Implementation Notes
1. Create new branch: `docs-cleanup`
2. Make incremental commits for each phase
3. Update AGENTS.md after changes
4. Run grep/rg to find any broken doc references
5. Update any code comments pointing to moved docs

## Timeline
- Total effort: 5 days
- Can be done incrementally
- Priority: Fix DI documentation first (it's causing confusion)
