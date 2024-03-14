from collections.abc import AsyncGenerator
from inspect import Parameter
from typing import Annotated, Final

from taskiq import AsyncBroker, Context, TaskiqDepends

from dishka import AsyncContainer
from dishka.integrations.base import wrap_injection

CONTAINER_NAME: Final = "dishka_container"


async def _open_container(
    context: Annotated[Context, TaskiqDepends()],
) -> AsyncGenerator[AsyncContainer, None]:
    container: AsyncContainer = context.state.dishka_container
    
    async with container() as new_container:
        yield new_container


def inject(func):
    annotation = Annotated[AsyncContainer, TaskiqDepends(_open_container)]
    additional_params = [Parameter(
        name=CONTAINER_NAME,
        annotation=annotation,
        kind=Parameter.KEYWORD_ONLY,
    )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda _, p: p[CONTAINER_NAME],
        additional_params=additional_params,
        is_async=True,
    )


def setup_broker(
    broker: AsyncBroker,
    container: AsyncContainer,
) -> None:
    broker.state.dishka_container = container
