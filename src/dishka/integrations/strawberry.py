__all__ = [
    "FromDishka",
    "inject",
]

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from inspect import (
    Parameter,
    isasyncgenfunction,
    iscoroutinefunction,
    signature,
)
from typing import ParamSpec, TypeVar, get_type_hints

from strawberry.types import Info

from dishka import (
    AsyncContainer,
    Container,
    FromDishka,
)
from .base import default_parse_dependency, wrap_injection

T = TypeVar("T")
P = ParamSpec("P")


DISHKA_INFO_PARAM = Parameter(
    name="___dishka_info",
    annotation=Info,
    kind=Parameter.KEYWORD_ONLY,
)


class ContainerSource(Enum):
    REQUEST = "request"


@dataclass(frozen=True)
class ContainerResult:
    container: AsyncContainer | Container
    source: ContainerSource | None = None


def _find_context_param(func: Callable[P, T]) -> str | None:
    hints = get_type_hints(func, include_extras=True)
    func_signature = signature(func)

    request_hint = None

    for name, hint in hints.items():
        param = func_signature.parameters.get(name)
        if param is None:
            continue
        if default_parse_dependency(param, hint) is not None:
            continue
        if hint is Info:
            request_hint = name

    return request_hint


def _get_container_with_source(
    _: tuple,
    kwargs: dict,
    *,
    param_name: str | None,
) -> ContainerResult:
    if param_name and param_name in kwargs:
        return ContainerResult(
            container=kwargs[param_name].state.dishka_container,
        )

    return ContainerResult(
        container=(
            kwargs[DISHKA_INFO_PARAM.name]
            .context["request"]
            .state.dishka_container
        ),
        source=ContainerSource.REQUEST,
    )


def _wrap_strawberry_injection(
    *,
    func: Callable[P, T],
    is_async: bool,
) -> Callable[P, T]:
    param_name = _find_context_param(func)

    additional_params = [] if param_name else [DISHKA_INFO_PARAM]

    def container_getter(
        args: tuple,
        kwargs: dict,
    ) -> AsyncContainer | Container:
        result = _get_container_with_source(
            args,
            kwargs,
            param_name=param_name,
        )

        return result.container

    return wrap_injection(
        func=func,
        is_async=is_async,
        additional_params=additional_params,
        container_getter=container_getter,
    )


def inject(func: Callable[P, T]) -> Callable[P, T]:
    is_async = iscoroutinefunction(func) or isasyncgenfunction(func)
    return _wrap_strawberry_injection(func=func, is_async=is_async)
