from collections.abc import Callable
from typing import Any, overload

from .decorator import Decorator
from .make_factory import make_factory


@overload
def decorate(
        *,
        provides: Any = None,
) -> Callable[[Callable], Decorator]:
    ...


@overload
def decorate(
        source: Callable | type,
        *,
        provides: Any = None,
) -> Decorator:
    ...


def decorate(
        source: Callable | type | None = None,
        provides: Any = None,
) -> Decorator | Callable[[Callable], Decorator]:
    if source is not None:
        return Decorator(make_factory(
            provides=provides, scope=None, source=source, cache=False,
        ))

    def scoped(func):
        return Decorator(make_factory(
            provides=provides, scope=None, source=func, cache=False,
        ))

    return scoped
