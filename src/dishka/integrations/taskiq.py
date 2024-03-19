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

from dishka import AsyncContainer
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
        container = await self._container().__aenter__()
        message.labels[CONTAINER_NAME] = container
        return message

    async def post_execute(
        self,
        message: TaskiqMessage,
        result: TaskiqResult[Any],
    ) -> None:
        await message.labels[CONTAINER_NAME].close()


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


def setup_broker(
    broker: AsyncBroker,
    container: AsyncContainer,
) -> None:
    broker.add_middlewares(ContainerMiddleware(container))
