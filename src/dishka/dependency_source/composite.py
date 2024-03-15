from collections.abc import Callable, Sequence
from typing import Any

from .alias import Alias
from .context_var import ContextVariable
from .decorator import Decorator
from .factory import Factory

DependencySource = Alias | Factory | Decorator | ContextVariable


class CompositeDependencySource:
    def __init__(
            self,
            origin: Callable,
            dependency_sources: Sequence[DependencySource] = (),
    ) -> None:
        self.dependency_sources = list(dependency_sources)
        self.origin = origin

    def __get__(self, instance, owner) -> "CompositeDependencySource":
        return CompositeDependencySource(
            origin=self.origin.__get__(instance, owner),
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
