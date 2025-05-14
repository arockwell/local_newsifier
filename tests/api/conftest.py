"""Pytest configuration for API tests."""

import pytest
from tests.fixtures.event_loop import event_loop_fixture

# Re-export the event_loop_fixture so it's available to all API tests
__all__ = ['event_loop_fixture']
