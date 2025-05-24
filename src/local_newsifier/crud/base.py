"""Base CRUD module with generic CRUD operations for SQLModel."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlmodel import Session, SQLModel, select

from local_newsifier.monitoring.decorators import monitor_db_query

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
        # Get table name from model
        table_name = getattr(self.model, "__tablename__", self.model.__name__.lower())

        @monitor_db_query(operation="select", table=table_name)
        def _get():
            return db.exec(select(self.model).where(self.model.id == id)).first()

        return _get()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get multiple items with pagination.

        Args:
            db: Database session
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of items
        """
        # Get table name from model
        table_name = getattr(self.model, "__tablename__", self.model.__name__.lower())

        @monitor_db_query(operation="select", table=table_name)
        def _get_multi():
            return db.exec(select(self.model).offset(skip).limit(limit)).all()

        return _get_multi()

    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """Create a new item.

        Args:
            db: Database session
            obj_in: Item data as dict or model instance

        Returns:
            Created item
        """
        # Get table name from model
        table_name = getattr(self.model, "__tablename__", self.model.__name__.lower())

        @monitor_db_query(operation="insert", table=table_name)
        def _create():
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

        return _create()

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
        # Get table name from model
        table_name = getattr(self.model, "__tablename__", self.model.__name__.lower())

        @monitor_db_query(operation="update", table=table_name)
        def _update():
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

        return _update()

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Remove an item.

        Args:
            db: Database session
            id: Item id

        Returns:
            Removed item if found, None otherwise
        """
        # Get table name from model
        table_name = getattr(self.model, "__tablename__", self.model.__name__.lower())

        @monitor_db_query(operation="delete", table=table_name)
        def _remove():
            db_obj = db.exec(select(self.model).where(self.model.id == id)).first()
            if db_obj:
                db.delete(db_obj)
                db.commit()
                return db_obj
            return None

        return _remove()
