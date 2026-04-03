import asyncio
from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any, Protocol, TypeAlias

from dishka.entities.key import CompilationKey


class _Pending:
    """Sentinel placed in the cache while an async factory is being resolved.

    If a concurrent coroutine (from asyncio.gather) tries to resolve the same
    dependency, it finds this sentinel and awaits the embedded Future instead
    of creating a duplicate.
    """

    __slots__ = ("_future",)

    def __init__(self) -> None:
        loop = asyncio.get_running_loop()
        self._future: asyncio.Future[Any] = loop.create_future()

    def set_result(self, value: Any) -> None:
        self._future.set_result(value)

    def set_exception(self, exc: BaseException) -> None:
        self._future.set_exception(exc)

    def __await__(self) -> Generator[Any, None, Any]:  # type: ignore[override]
        return self._future.__await__()


Exit: TypeAlias = tuple[
    Generator[Any, Any, Any] | None,
    AsyncGenerator[Any, Any] | None,
]


class CompiledFactory(Protocol):
    @abstractmethod
    def __call__(
        self,
        getter: Callable[[CompilationKey], Any] | None,
        exits: list[Exit],
        cache: Any,
        context: Any,
        container: Any,
    ) -> Any:
        raise NotImplementedError
