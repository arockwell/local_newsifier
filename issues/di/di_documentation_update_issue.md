# Issue: DI Documentation Update

## Title
Update and Standardize Dependency Injection Documentation

## Description
While we have implemented a robust dependency injection (DI) system throughout our codebase, the documentation of this system is incomplete. This issue focuses on creating comprehensive documentation that explains our DI patterns, conventions, and best practices to ensure consistent usage across the project and make onboarding new developers easier.

## Current Status
- Basic DI documentation exists in `docs/dependency_injection.md`
- Various DI patterns are used across the codebase
- Tool registration documentation in `docs/dependency_injection_tools.md`
- Missing comprehensive examples and guidelines

## Tasks
1. Update main DI documentation with latest patterns:
   - Document the complete lifecycle of container setup and usage
   - Explain service registration patterns (singleton vs transient)
   - Document dependency resolution and circular dependency handling
   - Add container extension and customization guidelines

2. Document standard patterns and conventions:
   - Service registration naming conventions
   - Factory vs direct registration differences
   - Parameterized factories usage
   - Lazy loading and dependency resolution

3. Create usage examples for different contexts:
   - API routes DI usage
   - CLI commands DI usage
   - Service-to-service DI access
   - Flow-to-service DI patterns
   - Task context DI handling

4. Document error handling and fallback patterns:
   - How to handle unavailable dependencies
   - Fallback mechanisms for graceful degradation
   - Error logging and reporting for DI issues
   - Troubleshooting common DI problems

5. Create onboarding guide section:
   - Quick start for new developers
   - Common patterns to follow
   - Anti-patterns to avoid
   - Extending the system with new services

## Acceptance Criteria
- All DI documentation is updated to reflect current patterns
- Clear examples are provided for all common usage scenarios
- Best practices are documented with explanations
- Documentation includes troubleshooting guides
- Standard patterns are defined for future development

## Technical Context
- The DI container is implemented in `src/local_newsifier/di_container.py`
- Container initialization happens in `src/local_newsifier/container.py`
- Each component type (services, flows, tools) has specific patterns
