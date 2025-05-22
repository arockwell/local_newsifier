import pytest
from sqlmodel import SQLModel
from local_newsifier.database.async_engine import AsyncDatabase
from tests.ci_skip_config import ci_skip_async


@ci_skip_async
@pytest.mark.asyncio
async def test_async_endpoint():
    """Test async endpoint with proper isolation."""
    # Create isolated test database
    db = AsyncDatabase("sqlite+aiosqlite:///:memory:")
    await db.initialize()
    await db.run_sync(lambda engine: SQLModel.metadata.create_all(engine))
    
    # Example async test logic with actual database interaction
    async with db.get_session() as session:
        assert session is not None
    
    # Cleanup
    await db.run_sync(lambda engine: SQLModel.metadata.drop_all(engine))
    await db.dispose()

