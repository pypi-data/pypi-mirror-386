"""Client-facing service APIs and shared models for dc43."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["contracts", "data_products", "data_quality", "governance", "odps"]


def __getattr__(name: str) -> Any:
    if name in __all__:
        module = import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
