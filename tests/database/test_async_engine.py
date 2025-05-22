import asyncio
import threading
from typing import Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Field, Session, select

from local_newsifier.database.async_engine import AsyncDatabase
from tests.fixtures.async_utils import isolated_event_loop


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str


@pytest.mark.asyncio
async def test_thread_isolation(isolated_event_loop):
    db = AsyncDatabase("sqlite:///:memory:")
    await db.initialize()
    await db.run_sync(lambda: SQLModel.metadata.create_all(db._engine))

    loop_thread = threading.get_ident()
    worker_thread = await db.run_sync(threading.get_ident)
    assert worker_thread != loop_thread

    await db.dispose()


@pytest.mark.asyncio
async def test_concurrent_operations(isolated_event_loop):
    db = AsyncDatabase("sqlite:///:memory:")
    await db.initialize()
    await db.run_sync(lambda: SQLModel.metadata.create_all(db._engine))

    async def insert_one(value: str):
        async with db.get_session() as session:
            await session.db.run_sync(lambda: session.session.add(Item(name=value)))
            await session.async_commit()

    await asyncio.gather(*(insert_one(f"item{i}") for i in range(5)))

    async with db.get_session() as session:
        items = await session.async_fetch_all(select(Item))
    assert len(items) == 5

    await db.dispose()


@pytest.mark.asyncio
async def test_error_handling_and_cleanup(isolated_event_loop):
    db = AsyncDatabase("sqlite:///:memory:")
    await db.initialize()
    await db.run_sync(lambda: SQLModel.metadata.create_all(db._engine))

    with pytest.raises(ValueError):
        async with db.get_session() as session:
            await session.db.run_sync(lambda: session.session.add(Item(name="bad")))
            raise ValueError("boom")

    async with db.get_session() as session:
        items = await session.async_fetch_all(select(Item))
    assert items == []

    await db.dispose()


@pytest.mark.asyncio
async def test_fastapi_compatibility(isolated_event_loop):
    db = AsyncDatabase("sqlite:///:memory:")
    await db.initialize()
    await db.run_sync(lambda: SQLModel.metadata.create_all(db._engine))

    async def add_item():
        def _add():
            with Session(db._engine) as s:
                s.add(Item(name="foo"))
                s.commit()
        return await db.run_sync(_add)

    await add_item()

    app = FastAPI()

    @app.get("/items")
    async def get_items():
        async with db.get_session() as session:
            return await session.async_fetch_all(select(Item))

    with TestClient(app) as client:
        response = client.get("/items")
        assert response.status_code == 200
        assert len(response.json()) == 1

    await db.dispose()
