# Testing Guidelines

This directory contains the test suite for Local Newsifier. When writing tests for async code, follow these guidelines:

- **Isolate the event loop**. Use the `isolated_event_loop` fixture from `tests.fixtures.async_utils` so each test gets its own loop.
- **Run async tests with `async_test`**. Decorate async tests with `@async_test` to automatically run them inside the provided loop.
- **Mock async dependencies**. Use `AsyncMockSession` or similar helpers to simulate async database interactions without hitting a real database.
- **CI Compatibility**. Avoid flaky behaviour by ensuring all tasks are awaited and the event loop is cleaned up. The provided fixtures are safe for parallel CI runs.

For more details on running tests and configuring the environment see `docs/testing_guide.md`.

