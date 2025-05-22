# CLI Tests Guide

CLI tests cover the command line interface defined in `src/local_newsifier/cli`.
`conftest.py` exposes fixtures for mocking session and feed services.

Use mocks from `tests/utils` to replace providers when invoking CLI commands.
Refer to `../CLAUDE.md` for the shared testing guidelines.
