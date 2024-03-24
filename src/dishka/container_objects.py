from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from .dependency_source import FactoryType


@dataclass
class Exit:
    __slots__ = ("type", "callable")
    type: FactoryType
    callable: Callable


class CompiledFactory(Protocol):
    @abstractmethod
    def __call__(
            self, getter: Callable, exits: list[Exit], context: Any,
    ) -> Any:
        raise NotImplementedError
