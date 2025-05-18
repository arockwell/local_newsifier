"""Asyncio event loop fixtures for injectable component tests."""

import asyncio
from contextlib import contextmanager
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi_injectable import register_app, get_injected_obj


@contextmanager
def _event_loop_context() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create a dedicated event loop and clean it up afterwards."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()


@pytest.fixture
def event_loop_fixture() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Provide a fresh event loop for each test."""
    with _event_loop_context() as loop:
        yield loop


@pytest.fixture
def injectable_app(event_loop_fixture):
    """Create a FastAPI app registered with fastapi-injectable."""
    app = FastAPI()
    event_loop_fixture.run_until_complete(register_app(app))
    yield app


@pytest.fixture
def injectable_service_fixture(event_loop_fixture):
    """Return a helper for injecting services using fastapi-injectable."""

    def get_injected_service(service_factory, *args, **kwargs):
        with _event_loop_context() as loop:
            return loop.run_until_complete(
                get_injected_obj(service_factory, args=list(args), kwargs=kwargs)
            )

    return get_injected_service
