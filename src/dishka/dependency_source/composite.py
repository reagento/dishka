from collections.abc import Callable, Sequence
from typing import Any

from .alias import Alias
from .context_var import ContextVariable
from .decorator import Decorator
from .factory import Factory

DependencySource = Alias | Factory | Decorator | ContextVariable


class CompositeDependencySource:
    _instances = 0

    def __init__(
            self,
            origin: Callable,
            dependency_sources: Sequence[DependencySource] = (),
    ) -> None:
        self.dependency_sources = list(dependency_sources)
        self.origin = origin
        CompositeDependencySource._instances += 1
        self.number = self._instances

    def __get__(self, instance, owner) -> "CompositeDependencySource":
        try:
            origin = self.origin.__get__(instance, owner)
        except AttributeError:  # not a valid descriptor
            origin = self.origin
        return CompositeDependencySource(
            origin=origin,
            dependency_sources=[
                s.__get__(instance, owner) for s in self.dependency_sources
            ],
        )

    def __call__(self, *args, **kwargs) -> Any:
        return self.origin(*args, **kwargs)


def ensure_composite(
        origin: Callable | CompositeDependencySource,
) -> CompositeDependencySource:
    if isinstance(origin, CompositeDependencySource):
        return origin
    else:
        return CompositeDependencySource(origin)
