# Services Tests Guide

Service tests validate business logic and integrations. `conftest.py` mocks
imports to avoid heavy dependencies like SQLite.

Use the injectable helpers from `tests/conftest_injectable.py` when mocking
providers. See `../CLAUDE.md` for global policies.
