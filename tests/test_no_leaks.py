import inspect
import importlib
import pkgutil

import os
import sqlmodel

os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "1")


def walk_services():
    for _, modname, _ in pkgutil.walk_packages(['src/local_newsifier/services'], prefix='local_newsifier.services.'):
        module = importlib.import_module(modname)
        for obj in module.__dict__.values():
            if inspect.isfunction(obj):
                yield obj


def test_no_sqlmodel_returned():
    for func in walk_services():
        ann = inspect.signature(func).return_annotation
        if ann is inspect.Signature.empty:
            continue
        bad = inspect.isclass(ann) and issubclass(ann, sqlmodel.SQLModel) and not ann.__name__.endswith('Read')
        assert not bad, f"{func.__qualname__} returns DB model {ann}"
