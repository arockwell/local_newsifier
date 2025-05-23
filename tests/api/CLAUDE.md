# API Tests Guide

Tests in this folder verify FastAPI endpoints and dependency wiring.
`conftest.py` defines any API specific fixtures. For mocking injectable
providers, use the helpers in `tests/conftest_injectable.py`.

See `../CLAUDE.md` for overall testing conventions.
