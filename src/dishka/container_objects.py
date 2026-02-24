from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any, Protocol, TypeAlias

from dishka.entities.key import DependencyKey

Exit: TypeAlias = tuple[
    Generator[Any, Any, Any] | None,
    AsyncGenerator[Any, Any] | None,
]


class CompiledFactory(Protocol):
    @abstractmethod
    def __call__(
            self,
            getter: Callable[[DependencyKey], Any] | None,
            exits: list[Exit],
            cache: Any,
            context: Any,
            container: Any,
    ) -> Any:
        raise NotImplementedError
