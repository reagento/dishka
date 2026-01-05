from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from dishka.entities.factory_type import FactoryType
from dishka.entities.scope import BaseScope


@dataclass(slots=True)
class Exit:
    type: FactoryType
    callable: Callable[..., Any]


class CompiledFactory(Protocol):
    @abstractmethod
    def __call__(
            self,
            getter: Callable[..., Any],
            exits: list[Exit],
            context: Any,
    ) -> Any:
        raise NotImplementedError

    @property
    @abstractmethod
    def scope(self) -> BaseScope:
        raise NotImplementedError