__all__ = ["inject"]

from collections.abc import Callable
from typing import Any, Final, ParamSpec, TypeVar, cast

from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection

T = TypeVar("T")
P = ParamSpec("P")
TWO: Final = 2
CONTAINER_NAME: Final = "dishka_container"


def _container_getter(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> AsyncContainer:
    if len(args) == 0:
        container = kwargs[CONTAINER_NAME]
    elif len(args) == TWO:
        container = args[-1].middleware_data[CONTAINER_NAME]
    else:
        container = args[2].middleware_data[CONTAINER_NAME]
    # typing.cast is used because middleware_data is not typed
    return cast(AsyncContainer, container)


def inject(func: Callable[P, T]) -> Callable[P, T]:
    return wrap_injection(
        func=func,
        is_async=True,
        container_getter=_container_getter,
    )
