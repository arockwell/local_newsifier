from __future__ import annotations

from sqlmodel import SQLModel

class FromModel(SQLModel):
    @classmethod
    def from_model(cls, obj: SQLModel) -> "FromModel":  # type: ignore[name-defined]
        """Safe detach inside a session."""
        return cls.model_validate(obj, from_attributes=True)
