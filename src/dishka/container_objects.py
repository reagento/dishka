from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any, Protocol, TypeAlias

Exit: TypeAlias = tuple[Generator | None, AsyncGenerator | None]


class CompiledFactory(Protocol):
    @abstractmethod
    def __call__(
            self,
            getter: Callable[..., Any],
            exits: list[Exit],
            cache: Any,
            context: Any,
    ) -> Any:
        raise NotImplementedError
