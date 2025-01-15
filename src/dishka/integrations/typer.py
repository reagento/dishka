"""Integration for Typer https://typer.tiangolo.com"""

__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable
from inspect import Parameter
from typing import Final, ParamSpec, TypeVar, cast, get_type_hints

import click
import typer

from dishka import Container, FromDishka, Scope
from dishka.dependency_source.make_context_var import from_context
from dishka.provider import Provider
from .base import is_dishka_injected, wrap_injection

T = TypeVar("T")
P = ParamSpec("P")
CONTAINER_NAME: Final = "dishka_container"
CONTAINER_NAME_REQ: Final = "dishka_container_req"


def inject(func: Callable[P, T]) -> Callable[P, T]:
    hints = get_type_hints(func)
    context_hint = next(
        (name for name, hint in hints.items() if hint is typer.Context),
        None,
    )
    if context_hint is None:
        additional_params = [
            Parameter(
                name="___dishka_context",
                annotation=typer.Context,
                kind=Parameter.KEYWORD_ONLY,
            ),
        ]
    else:
        additional_params = []

    param_name = context_hint or "___dishka_context"

    def get_container(_, p):
        context: typer.Context = p[param_name]
        container = context.meta[CONTAINER_NAME]

        req_container = context.with_resource(
            container({typer.Context: context}, scope=Scope.REQUEST),
        )
        context.meta[CONTAINER_NAME_REQ] = req_container
        return req_container

    return wrap_injection(
        func=func,
        is_async=False,
        additional_params=additional_params,
        container_getter=get_container,
    )


def _inject_commands(app: typer.Typer) -> None:
    for command in app.registered_commands:
        if command.callback is not None and not is_dishka_injected(
            command.callback,
        ):
            command.callback = inject(command.callback)

    for group in app.registered_groups:
        if group.typer_instance is not None:
            _inject_commands(group.typer_instance)


class TyperProvider(Provider):
    context = from_context(provides=typer.Context, scope=Scope.APP)


def setup_dishka(
    container: Container,
    app: typer.Typer,
    *,
    finalize_container: bool = True,
    auto_inject: bool = False,
) -> None:
    @app.callback()
    def inject_dishka_container(context: typer.Context) -> None:
        context.meta[CONTAINER_NAME] = container

        if finalize_container:
            context.call_on_close(container.close)

    if auto_inject:
        _inject_commands(app)
