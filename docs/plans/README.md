# Local Newsifier Knowledge Base

This directory contains comprehensive knowledge documentation consolidated from GitHub issues, organized by topic area. These documents serve as the authoritative source for understanding project decisions, patterns, and implementation strategies.

## Document Organization

### Core Integration Areas

#### [Apify Integration](./apify-integration.md)
- Webhook implementation patterns
- Actor configuration and management
- Schedule synchronization
- Data transformation strategies
- Testing approaches
- Future enhancement plans

#### [Dependency Injection Architecture](./dependency-injection-architecture.md)
- Migration from DIContainer to fastapi-injectable
- Provider function patterns
- Anti-patterns to avoid
- Event loop management
- Testing strategies
- Migration checklist

#### [Async to Sync Migration](./async-to-sync-migration.md)
- Rationale for moving from async to sync routes
- Migration scope and steps
- Implementation plan and checklist
- Benefits and risk mitigation

### Development Practices

#### [Documentation Strategy](./documentation-strategy.md)
- Documentation philosophy and principles
- Structure and organization
- Documentation types (ADRs, diagrams, API docs)
- Standards and patterns
- Maintenance and quality checks

#### [CLI Development](./cli-development.md)
- Command structure and patterns
- Dependency injection in CLI
- Output formatting strategies
- Error handling patterns
- Testing approaches
- Advanced features and future enhancements

### System Improvements

#### [Enhancement Roadmap](./enhancement-roadmap.md)
- Performance and scalability improvements
- Development experience enhancements
- Data processing capabilities
- User interface features
- Integration expansions
- Machine learning enhancements
- Security improvements

#### [Technical Debt Reduction](./technical-debt-reduction.md)
- Dependency management issues
- Test infrastructure problems
- Code quality concerns
- Performance bottlenecks
- Error handling gaps
- Prioritization matrix
- Remediation roadmap

## How to Use This Knowledge Base

### For New Features
1. Check relevant topic documents for existing patterns
2. Follow established conventions and best practices
3. Update documentation when adding new patterns

### For Bug Fixes
1. Review technical debt document for known issues
2. Check if the bug relates to documented problems
3. Follow remediation strategies if available

### For Refactoring
1. Consult architecture documents for target patterns
2. Follow migration strategies where documented
3. Update knowledge base with learnings

### For Planning
1. Review enhancement roadmap for planned features
2. Check technical debt priorities
3. Align new work with documented strategies

## Knowledge Management

### Adding New Knowledge
When documenting new patterns or decisions:
1. Add to the appropriate existing document if it fits
2. Create a new document for major new areas
3. Update this README with the new document
4. Cross-reference related documents

### Keeping Knowledge Current
- Update documents when patterns change
- Mark deprecated patterns clearly
- Add dates to time-sensitive information
- Link to relevant pull requests and issues

### Knowledge Sources
These documents consolidate information from:
- 93+ GitHub issues
- Pull request discussions
- Code review feedback
- Implementation experiences
- Architecture decisions

## Quick Reference

### Critical Patterns

**Dependency Injection**:
```python
@injectable(use_cache=False)
def get_service(dep: Annotated[Dep, Depends(get_dep)]):
    from module import Service
    return Service(dep)
```

**Error Handling**:
```python
@with_retry(RetryPolicy(max_attempts=3))
def operation():
    # Automatic retry with exponential backoff
```

**Testing**:
```python
def test_with_mock(mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    # Test code
```

**CLI Commands**:
```python
@cli.command()
def command(service: Annotated[Service, Depends(get_service)]):
    # Command implementation
```

### Common Issues

| Issue | Document | Section |
|-------|----------|---------|
| Event loop errors | Technical Debt | Event Loop Issues |
| Circular imports | Technical Debt | Circular Dependencies |
| Offline install fails | Technical Debt | Offline Installation Issues |
| DI migration | Dependency Injection | Migration Strategy |
| Webhook testing | Apify Integration | Testing Strategies |

## Related Documentation

- [Project README](../../README.md) - Project overview
- [CLAUDE.md](../../CLAUDE.md) - AI assistant instructions
- [API Documentation](../api/) - API reference
- [Architecture Docs](../architecture/) - System design

## Contributing

When contributing to these documents:
1. Ensure information is accurate and tested
2. Include code examples from the actual codebase
3. Link to relevant issues and PRs
4. Keep language clear and concise
5. Update the index when adding new sections
