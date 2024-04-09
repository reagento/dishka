__all__ = (
    "FromDishka",
    "inject",
    "setup_dishka",
)

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from faststream import BaseMiddleware, FastStream, context
from faststream.broker.message import StreamMessage
from faststream.utils.context.repository import ContextRepo

from dishka import AsyncContainer, FromDishka
from dishka.integrations.base import wrap_injection

T = TypeVar("T")


def inject(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    return wrap_injection(
        func=func,
        container_getter=lambda *_: context.get_local("dishka"),
        is_async=True,
        remove_depends=True,
    )


class DishkaMiddleware(BaseMiddleware):
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    def __call__(self, msg: Any | None = None) -> "DishkaMiddleware":
        self.msg = msg
        return self

    async def consume_scope(
            self,
            call_next: Callable[[Any], Awaitable[Any]],
            message: Any,
    ) -> Any:
        async with self.container({
            StreamMessage: message,
            type(message): message,
            ContextRepo: context,
        }) as request_container:
            with context.scope("dishka", request_container):
                return await call_next(message)


def setup_dishka(
        container: AsyncContainer,
        app: FastStream,
        *,
        finalize_container: bool = True,
        auto_inject: bool = False,
) -> None:
    assert app.broker, "You can't patch FastStream application without broker"  # noqa: S101

    if finalize_container:
        app.after_shutdown(container.close)

    if auto_inject:
        app.broker._call_decorators = (inject,)  # noqa: SLF001

    app.broker._middlewares = (  # noqa: SLF001
        *app.broker._middlewares,  # noqa: SLF001
        DishkaMiddleware(container),
    )
    app.broker.setup()
