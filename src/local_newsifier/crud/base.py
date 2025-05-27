"""Base CRUD module with generic CRUD operations for SQLModel."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlmodel import Session, SQLModel, select

# Type for the model class - doesn't need to be bound to TableBase anymore
ModelType = TypeVar("ModelType", bound=SQLModel)


class CRUDBase(Generic[ModelType]):
    """Base class for CRUD operations."""

    def __init__(self, model: Type[ModelType]):
        """Initialize with model class.

        Args:
            model: SQLModel model class
        """
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get an item by id.

        Args:
            db: Database session
            id: Item id

        Returns:
            The item if found, None otherwise
        """
        return db.exec(select(self.model).where(self.model.id == id)).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple items with pagination.

        Args:
            db: Database session
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of items
        """
        return db.exec(select(self.model).offset(skip).limit(limit)).all()

    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """Create a new item.

        Args:
            db: Database session
            obj_in: Item data as dict or model instance

        Returns:
            Created item
        """
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            # Use only SQLModel's model_dump method
            obj_data = obj_in.model_dump()

        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[Dict[str, Any], ModelType]
    ) -> ModelType:
        """Update an item.

        Args:
            db: Database session
            db_obj: Database object to update
            obj_in: Update data as dict or model instance

        Returns:
            Updated item
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Use only SQLModel's model_dump method
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Remove an item.

        Args:
            db: Database session
            id: Item id

        Returns:
            Removed item if found, None otherwise
        """
        db_obj = db.exec(select(self.model).where(self.model.id == id)).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return db_obj
        return None
