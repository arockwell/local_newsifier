# Migration Plans

This directory contains active migration plans and technical debt tracking for the Local Newsifier project.

## Active Documents

### [Service Layer Migration](./service-layer-migration.md)
- Service layer patterns and best practices
- Sync-only implementation guidelines
- Dependency injection patterns
- Testing strategies

### [Technical Debt Reduction](./technical-debt-reduction.md)
- Current technical debt inventory
- Prioritization matrix
- Remediation strategies
- Progress tracking

## Architecture Decision: Sync-Only Implementation

The project uses **synchronous patterns exclusively** throughout the codebase. This decision was made to:
- Prioritize development simplicity and maintainability
- Avoid complexity of mixed async/sync patterns
- Reduce cognitive overhead for developers
- Eliminate event loop and testing issues

**Important**: Do not introduce async patterns in new code. All new development should follow synchronous patterns as documented in CLAUDE.md.

## Related Documentation

- [Project README](../../README.md) - Project overview
- [CLAUDE.md](../../CLAUDE.md) - AI assistant instructions
- [Architecture Overview](../architecture/overview.md) - System design
- [Guides](../guides/) - Development guides
