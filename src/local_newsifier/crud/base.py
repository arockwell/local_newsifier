"""Base CRUD module with generic CRUD operations."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy.orm import Session

from local_newsifier.models.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
SchemaType = TypeVar("SchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, SchemaType]):
    """Base class for CRUD operations."""

    def __init__(self, model: Type[ModelType], schema: Type[SchemaType]):
        """Initialize with model class and schema class.

        Args:
            model: SQLAlchemy model class
            schema: Pydantic schema class for returning data
        """
        self.model = model
        self.schema = schema

    def get(self, db: Session, id: int) -> Optional[SchemaType]:
        """Get an item by id.

        Args:
            db: Database session
            id: Item id

        Returns:
            The item if found, None otherwise
        """
        db_obj = db.query(self.model).filter(self.model.id == id).first()
        return self.schema.model_validate(db_obj) if db_obj else None

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[SchemaType]:
        """Get multiple items with pagination.

        Args:
            db: Database session
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of items
        """
        db_objs = db.query(self.model).offset(skip).limit(limit).all()
        return [self.schema.model_validate(obj) for obj in db_objs]

    def create(
        self, db: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> SchemaType:
        """Create a new item.

        Args:
            db: Database session
            obj_in: Item create data

        Returns:
            Created item
        """
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            obj_data = obj_in.model_dump()

        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return self.schema.model_validate(db_obj)

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> SchemaType:
        """Update an item.

        Args:
            db: Database session
            db_obj: Database object to update
            obj_in: Update data

        Returns:
            Updated item
        """
        obj_data = db_obj.model_dump()

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return self.schema.model_validate(db_obj)

    def remove(self, db: Session, *, id: int) -> Optional[SchemaType]:
        """Remove an item.

        Args:
            db: Database session
            id: Item id

        Returns:
            Removed item if found, None otherwise
        """
        db_obj = db.query(self.model).filter(self.model.id == id).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return self.schema.model_validate(db_obj)
        return None
