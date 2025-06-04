# Documentation Index

Welcome to the Local Newsifier documentation. This directory contains comprehensive guides for developers, operators, and contributors.

## 📁 Documentation Structure

### 🏗️ Architecture
- [Architecture Overview](architecture/overview.md) - System design and architecture decisions

### 📖 Guides
- [CLI Usage](guides/cli_usage.md) - Complete CLI command reference
- [Dependency Injection](guides/dependency_injection.md) - DI patterns and migration status
- [Error Handling](guides/error_handling.md) - Error handling patterns and best practices
- [Offline Installation](guides/offline_installation.md) - Installing without internet access
- [Python Setup](guides/python_setup.md) - Development environment setup
- [Testing Guide](guides/testing_guide.md) - Comprehensive testing documentation

### 🔌 Integrations
- [Apify Integration](integrations/apify.md) - Web scraping with Apify

### 🚀 Operations
- [Database Guide](operations/database.md) - Database setup and management
- [Deployment Guide](operations/deployment.md) - Deployment and CI/CD

### 📋 Migration Plans
- [Active Migrations](migration-plans/README.md) - Current migration efforts and checklists

## 🎯 Quick Links

### For Developers
- Start with [Python Setup](guides/python_setup.md)
- Review [Architecture Overview](architecture/overview.md)
- Learn [CLI Commands](guides/cli_usage.md)
- Understand [Testing](guides/testing_guide.md)

### For Operations
- [Deployment Guide](operations/deployment.md)
- [Database Management](operations/database.md)
- [Offline Installation](guides/offline_installation.md)

### For Contributors
- [Testing Guide](guides/testing_guide.md)
- [Error Handling](guides/error_handling.md)
- [Dependency Injection](guides/dependency_injection.md)

## 📚 Documentation Standards

### File Organization
- **Guides**: How-to documentation for specific tasks
- **Architecture**: System design and architectural decisions
- **Operations**: Deployment, monitoring, and maintenance
- **Integrations**: External service integrations
- **Migration Plans**: Active migration efforts

### Writing Guidelines
1. Use clear, descriptive headings
2. Include practical examples
3. Add table of contents for long documents
4. Link to related documentation
5. Keep code examples up-to-date

### Maintenance
- Review quarterly for accuracy
- Update when code changes
- Archive completed migrations
- Remove outdated content

## 🔍 Finding Information

### Search Documentation
```bash
# Search all docs for a term
rg "webhook" docs/

# Find files by name
fd "test" docs/

# Search specific file types
rg "FastAPI" --type md docs/
```

### Get Help
- Check root [README.md](../README.md) for project overview
- Review [CLAUDE.md](../CLAUDE.md) for AI assistant instructions
- Open an issue for documentation improvements
