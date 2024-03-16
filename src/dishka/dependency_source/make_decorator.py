from collections.abc import Callable
from typing import Any, overload

from .composite import CompositeDependencySource, ensure_composite
from .decorator import Decorator
from .make_factory import make_factory
from .unpack_provides import unpack_decorator


def _decorate(
        source: Callable | type | None = None,
        provides: Any = None,
) -> CompositeDependencySource:
    composite = ensure_composite(source)
    decorator = Decorator(make_factory(
        provides=provides, scope=None, source=source, cache=False,
    ))
    composite.dependency_sources.extend(unpack_decorator(decorator))
    return composite


@overload
def decorate(
        *,
        provides: Any = None,
) -> Callable[[Callable], CompositeDependencySource]:
    ...


@overload
def decorate(
        source: Callable | type,
        *,
        provides: Any = None,
) -> CompositeDependencySource:
    ...


def decorate(
        source: Callable | type | None = None,
        provides: Any = None,
) -> CompositeDependencySource | Callable[
    [Callable], CompositeDependencySource]:
    if source is not None:
        return _decorate(source, provides)

    def scoped(func):
        return _decorate(func, provides)

    return scoped
