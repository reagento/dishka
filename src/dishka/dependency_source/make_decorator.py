from collections.abc import Callable
from typing import Any, overload

from .composite import CompositeDependencySource, ensure_composite
from .decorator import Decorator
from .make_factory import make_factory
from .unpack_provides import unpack_decorator


def _decorate(
        source: Callable | type | None = None,
        provides: Any = None,
        *,
        is_in_class: bool = True,
) -> CompositeDependencySource:
    composite = ensure_composite(source)
    decorator = Decorator(make_factory(
        provides=provides, scope=None, source=source, cache=False,
        is_in_class=is_in_class,
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
) -> Any:
    if source is not None:
        return _decorate(source, provides, is_in_class=True)

    def scoped(func):
        return _decorate(func, provides, is_in_class=True)

    return scoped


def decorate_on_instance(
        source: Callable | type | None = None,
        provides: Any = None,
) -> CompositeDependencySource:
    return _decorate(source, provides, is_in_class=False)

