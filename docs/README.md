# Local Newsifier Documentation

Welcome to the Local Newsifier documentation. This directory contains comprehensive guides, architectural decisions, and operational documentation for the project.

## Documentation Structure

### 📚 [Guides](./guides/)
How-to guides and comprehensive documentation for developers.

- **[Dependency Injection Guide](./guides/dependency_injection.md)** - Complete guide to using fastapi-injectable
- **[Testing Guide](./guides/testing_guide.md)** - Comprehensive testing patterns and strategies
- **[Offline Installation Guide](./guides/offline_installation.md)** - Installing without internet access
- **[Offline Installation Troubleshooting](./guides/offline_installation_troubleshooting.md)** - Common issues and solutions
- **[Python Setup](./guides/python_setup.md)** - Development environment configuration
- **[Error Handling](./guides/error_handling.md)** - Error handling patterns and best practices
- **[Injectable Examples](./guides/injectable_examples.md)** - Code examples for dependency injection patterns
- **[Anti-Patterns Reference](./guides/dependency_injection_antipatterns.md)** - Common DI mistakes to avoid
- **[Testing Injectable Dependencies](./guides/testing_injectable_dependencies.md)** - Testing with dependency injection

### 🔌 [Integrations](./integrations/)
Documentation for external service integrations.

- **[Apify Integration](./integrations/apify/)**
  - [Integration Guide](./integrations/apify/integration.md) - Complete Apify setup
  - [Error Handling](./integrations/apify/error_handling.md) - Apify-specific error patterns
  - [Webhook Testing](./integrations/apify/webhook_testing.md) - Testing Apify webhooks
- **[Celery Integration](./integrations/celery_integration.md)** - Task queue setup (being phased out)

### 🛠 [Operations](./operations/)
Operational guides for deployment and maintenance.

- **[Database Initialization](./operations/db_initialization.md)** - Setting up the database
- **[Database Diagnostics](./operations/db_diagnostics.md)** - Troubleshooting database issues
- **[CI/PR Chains](./operations/ci_pr_chains.md)** - Continuous integration setup

### 📐 [Architecture](./architecture/)
Architectural decisions and migration documentation.

- **[DI Migration History](./archive/di_conversion_plan.md)** - Historical DI migration details
- **[Async to Sync Migration](./plans/async-to-sync-migration.md)** - Ongoing migration plan

### 📋 [Plans](./plans/)
Future development plans and proposals.

- **[FastAPI-Injectable Migration](./plans/fastapi-injectable-migration/)** - DI framework migration
- **[CLI to HTTP](./plans/cli_to_http/)** - CLI migration to HTTP endpoints
- **[Enhancement Roadmap](./plans/enhancement-roadmap.md)** - Future features
- **[Technical Debt Reduction](./plans/technical-debt-reduction.md)** - Code improvement plans
- See the [Plans README](./plans/README.md) for complete list

### 📦 [Archive](./archive/)
Historical documentation preserved for reference.

Contains completed migration plans, old documentation versions, and historical context.

### 📝 [Examples](./examples/)
Code examples and patterns.

- **[Conditional Decorator Example](./examples/conditional_decorator_example.py)** - Advanced decorator patterns

## Module-Specific Guides

- [API Guide](../src/local_newsifier/api/CLAUDE.md)
- [CLI Guide](../src/local_newsifier/cli/CLAUDE.md)
- [Database Guide](../src/local_newsifier/database/CLAUDE.md)
- [DI Guide](../src/local_newsifier/di/CLAUDE.md)
- [Flows Guide](../src/local_newsifier/flows/CLAUDE.md)
- [Models Guide](../src/local_newsifier/models/CLAUDE.md)
- [Services Guide](../src/local_newsifier/services/CLAUDE.md)
- [Tools Guide](../src/local_newsifier/tools/CLAUDE.md)

## Project Documentation

- [Main Development Guide](../CLAUDE.md) - Primary development guide
- [Project README](../README.md) - Project overview
- [CLI README](../README_CLI.md) - CLI usage guide
- [FastAPI-Injectable Migration Plan](../FastAPI-Injectable-Migration-Plan.md) - Migration details

## Quick Links

### For New Developers
1. Start with [Python Setup](./guides/python_setup.md)
2. Read the [Dependency Injection Guide](./guides/dependency_injection.md)
3. Review the [Testing Guide](./guides/testing_guide.md)

### For DevOps
1. [Database Initialization](./operations/db_initialization.md)
2. [Offline Installation Guide](./guides/offline_installation.md)
3. [CI/PR Chains](./operations/ci_pr_chains.md)

### For Contributors
1. [Testing Guide](./guides/testing_guide.md)
2. [Error Handling](./guides/error_handling.md)
3. [Anti-Patterns Reference](./guides/dependency_injection_antipatterns.md)

## Documentation Standards

### File Naming
- Use lowercase with underscores: `offline_installation.md`
- Be descriptive but concise
- Group related docs in subdirectories

### Content Structure
Each documentation file should include:
1. **Title** - Clear, descriptive title
2. **Overview** - Brief description of the topic
3. **Table of Contents** - For longer documents
4. **Main Content** - Well-organized sections
5. **Examples** - Practical code examples
6. **Troubleshooting** - Common issues (if applicable)
7. **See Also** - Related documentation links

### Maintenance
- Keep documentation up-to-date with code changes
- Archive outdated docs rather than deleting
- Test all code examples
- Review quarterly for accuracy

## Contributing to Documentation

When adding new documentation:
1. Place it in the appropriate directory
2. Update this README with a link
3. Follow the content structure guidelines
4. Include practical examples
5. Link to related documentation

For questions or suggestions about documentation, please open an issue on GitHub.
