"""Simplified fastapi-injectable stub used for testing."""
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def injectable(*, use_cache: bool | None = False, scope: Any | None = None) -> Callable[[T], T]:
    """Return a decorator that leaves the object unchanged."""
    def decorator(obj: T) -> T:
        return obj
    return decorator


async def register_app(app: Any) -> None:
    """Stub register_app that performs no initialization."""
    return None


def get_injected_obj(func: Callable[..., T], args: list | None = None, kwargs: dict | None = None) -> T:
    """Call ``func`` with the provided arguments."""
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    return func(*args, **kwargs)
