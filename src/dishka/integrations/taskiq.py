__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import AsyncGenerator, Callable, Generator
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

from dishka import AsyncContainer, FromDishka
from dishka.integrations.base import wrap_injection

CONTAINER_NAME: Final = "dishka_container"


class ContainerMiddleware(TaskiqMiddleware):
    def __init__(self, container: AsyncContainer) -> None:
        super().__init__()
        self._container = container

    async def pre_execute(
        self,
        message: TaskiqMessage,
    ) -> TaskiqMessage:
        message.labels[CONTAINER_NAME] = await self._container().__aenter__()
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
) -> Generator[AsyncGenerator, None, None]:
    yield context.message.labels[CONTAINER_NAME]


def inject(func: Callable[..., Any]) -> Callable[..., Any]:
    annotation = Annotated[
        AsyncContainer, TaskiqDepends(_get_container),
    ]
    additional_params = [Parameter(
        name=CONTAINER_NAME,
        annotation=annotation,
        kind=Parameter.KEYWORD_ONLY,
    )]

    return wrap_injection(
        func=func,
        is_async=True,
        remove_depends=True,
        additional_params=additional_params,
        container_getter=lambda _, p: p[CONTAINER_NAME],
    )


def setup_dishka(
    container: AsyncContainer,
    broker: AsyncBroker,
) -> None:
    broker.add_middlewares(ContainerMiddleware(container))
