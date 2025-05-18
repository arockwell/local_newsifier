import importlib
from typing import Callable

from fastapi_injectable import injectable


def make_provider(import_path: str, attr: str, *, name: str | None = None) -> Callable:
    """Create a simple provider function for the target object.

    Parameters
    ----------
    import_path:
        Module path to import.
    attr:
        Attribute within the module to return.
    name:
        Optional function name for the provider. If given, the returned
        function's ``__name__`` attribute is set accordingly so that
        ``str(provider)`` contains the expected identifier.

    Returns
    -------
    Callable
        Function wrapped with ``@injectable(use_cache=False)`` that imports
        and returns the specified attribute each time it is called.
    """

    def provider():
        module = importlib.import_module(import_path)
        return getattr(module, attr)

    provider.__name__ = name or provider.__name__
    return injectable(use_cache=False)(provider)
