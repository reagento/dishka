from dataclasses import dataclass
from enum import Enum
from typing import Any


@dataclass(slots=True)
class _ScopeValue:
    name: str
    skip: bool


def new_scope(value: str, *, skip: bool = False) -> _ScopeValue:
    return _ScopeValue(value, skip)


class BaseScope(Enum):
    __slots__ = ("name", "skip")

    def __init__(self, value: _ScopeValue) -> None:
        self.name = value.name  # type: ignore[misc]
        self.skip = value.skip


class Scope(BaseScope):
    RUNTIME = new_scope("RUNTIME", skip=True)
    APP = new_scope("APP")
    SESSION = new_scope("SESSION", skip=True)
    REQUEST = new_scope("REQUEST")
    ACTION = new_scope("ACTION")
    STEP = new_scope("STEP")


class InvalidScopes(BaseScope):
    UNKNOWN_SCOPE = new_scope("<unknown scope>", skip=True)

    def __str__(self) -> Any:
        return str(self.value.name)
