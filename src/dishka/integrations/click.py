__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from typing import Optional, Any

from click import (
    Command,
    Context,
    Group,
    get_current_context,
)

from dishka import Container, FromDishka, Scope
from .base import is_dishka_injected, wrap_injection

CONTAINER_NAME = "dishka_container"


def inject(func):
    return wrap_injection(
        func=func,
        container_getter=lambda _, __: get_current_context().meta[
            CONTAINER_NAME
        ],
        remove_depends=True,
        is_async=False,
    )


def _inject_commands(context: Context, command: Command) -> None:
    if isinstance(command, Command) and not is_dishka_injected(command.callback):
        command.callback = inject(command.callback)

    if isinstance(command, Group):
        for command_name in command.list_commands(context):
            child_command = command.get_command(context, command_name)
            _inject_commands(context, child_command)


class DishkaContext(Context):
    def __init__(
        self,
        *args: Any,
        dishka_container: Optional[Container] = None,
        dishka_auto_inject: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        request_container = self.with_resource(
            dishka_container({Context: self}, scope=Scope.REQUEST)
        )
        self.meta[CONTAINER_NAME] = request_container
        if dishka_auto_inject:
            _inject_commands(self, self.command)


def setup_dishka(
    container: Container,
    command: Command,
    *,
    auto_inject: bool = False,
) -> None:
    command.context_class = DishkaContext
    command.context_settings["dishka_container"] = container
    command.context_settings["dishka_auto_inject"] = auto_inject
