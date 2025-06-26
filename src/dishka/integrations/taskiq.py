__all__ = [
    "FromDishka",
    "TaskiqProvider",
    "inject",
    "setup_dishka",
]

import warnings
from collections.abc import Callable, Generator
from functools import partial
from inspect import Parameter
from typing import Annotated, Any, Final

from taskiq import (
    AsyncBroker,
    Context,
    TaskiqDepends,
    TaskiqMessage,
    TaskiqMiddleware,
    TaskiqResult,
)

from dishka import AsyncContainer, FromDishka, Provider, Scope, from_context
from dishka.integrations.base import wrap_injection

CONTAINER_NAME: Final = "dishka_container"


class TaskiqProvider(Provider):
    event = from_context(TaskiqMessage, scope=Scope.REQUEST)


class ContainerMiddleware(TaskiqMiddleware):
    def __init__(self, container: AsyncContainer) -> None:
        super().__init__()
        self._container = container

    async def pre_execute(
        self,
        message: TaskiqMessage,
    ) -> TaskiqMessage:
        message.labels[CONTAINER_NAME] = await self._container(
            context={TaskiqMessage: message},
        ).__aenter__()
        return message

    async def on_error(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
        exception: BaseException,
    ) -> None:
        if CONTAINER_NAME in result.labels:
            await result.labels[CONTAINER_NAME].close()
            del result.labels[CONTAINER_NAME]

    async def post_execute(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
    ) -> None:
        if CONTAINER_NAME in result.labels:
            await result.labels[CONTAINER_NAME].close()
            del result.labels[CONTAINER_NAME]


def _get_container(
    context: Annotated[Context, TaskiqDepends()],
) -> Generator[AsyncContainer, None, None]:
    yield context.message.labels[CONTAINER_NAME]


def inject(
    func: Callable[..., Any] | None = None,
    *,
    patch_module: bool = False,
) -> Callable[..., Any]:
    if func is None:
        return partial(_inject_wrapper, patch_module=patch_module)

    return _inject_wrapper(func, patch_module=patch_module)


def _inject_wrapper(
    func: Callable[..., Any],
    *,
    patch_module: bool,
) -> Callable[..., Any]:
    annotation = Annotated[
        AsyncContainer, TaskiqDepends(_get_container),
    ]
    additional_params = [Parameter(
        name=CONTAINER_NAME,
        annotation=annotation,
        kind=Parameter.KEYWORD_ONLY,
    )]

    wrapper = wrap_injection(
        func=func,
        is_async=True,
        remove_depends=True,
        additional_params=additional_params,
        container_getter=lambda _, p: p[CONTAINER_NAME],
    )

    if not patch_module:
        warnings.warn(
            "Behavior without patch module is deprecated"
            ", use patch_module = True",
            DeprecationWarning,
            stacklevel=2,
        )

        wrapper.__module__ = wrap_injection.__module__

    return wrapper


def setup_dishka(
    container: AsyncContainer,
    broker: AsyncBroker,
) -> None:
    broker.add_middlewares(ContainerMiddleware(container))
