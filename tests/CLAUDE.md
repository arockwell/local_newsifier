# Local Newsifier Test Suite Guide

This directory contains all automated tests. Tests are grouped by component type (API, CLI, flows, services, models, tools, and CRUD helpers).

## Fixtures and Utilities
- Common fixtures live in `tests/fixtures/` and `tests/utils/`.
- `event_loop_fixture` helps manage async code when using fastapi-injectable.
- Use the helpers in `conftest_injectable.py` to mock injectable dependencies.
- Skip problematic tests in CI with decorators from `ci_skip_config.py`.

Follow the testing guidance in `../claude.md` for additional details on coverage goals and patterns.
