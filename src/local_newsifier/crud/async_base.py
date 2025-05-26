"""Async base class for CRUD operations using SQLModel and async SQLAlchemy."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=SQLModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=SQLModel)


class AsyncCRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for async CRUD operations.

    This class provides common async database operations for SQLModel models.
    """

    def __init__(self, model: Type[ModelType]):
        """Initialize CRUD with model.

        Args:
            model: SQLModel model class
        """
        self.model = model

    async def get(self, session: AsyncSession, id: int) -> Optional[ModelType]:
        """Get a single record by ID.

        Args:
            session: Async database session
            id: Record ID

        Returns:
            Model instance or None
        """
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, session: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple records.

        Args:
            session: Async database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of model instances
        """
        result = await session.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, session: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record.

        Args:
            session: Async database session
            obj_in: Data for creating the record

        Returns:
            Created model instance
        """
        db_obj = self.model(**obj_in.model_dump())
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any],
    ) -> ModelType:
        """Update a record.

        Args:
            session: Async database session
            db_obj: Existing database object
            obj_in: Update data

        Returns:
            Updated model instance
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            setattr(db_obj, field, update_data[field])

        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def remove(self, session: AsyncSession, *, id: int) -> Optional[ModelType]:
        """Delete a record.

        Args:
            session: Async database session
            id: Record ID

        Returns:
            Deleted model instance or None
        """
        obj = await self.get(session, id)
        if obj:
            await session.delete(obj)
            await session.commit()
        return obj
