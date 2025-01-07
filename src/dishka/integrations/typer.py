"""Integration for Typer https://typer.tiangolo.com"""

__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable
from typing import Final, TypeVar

import typer
from click import get_current_context

from dishka import Container, FromDishka
from .base import is_dishka_injected, wrap_injection

T = TypeVar("T")
CONTAINER_NAME: Final = "dishka_container"


def inject(func: Callable[..., T]) -> Callable[..., T]:
    return wrap_injection(
        func=func,
        container_getter=lambda _, __: get_current_context().meta[
            CONTAINER_NAME
        ],
        remove_depends=True,
        is_async=False,
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
