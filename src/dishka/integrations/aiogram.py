__all__ = [
    "AutoInjectMiddleware",
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Container
from inspect import Parameter

from aiogram import BaseMiddleware, Router
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.types import TelegramObject

from dishka import AsyncContainer, FromDishka
from .base import is_dishka_injected, wrap_injection

CONTAINER_NAME = "dishka_container"


def inject(func):
    additional_params = [Parameter(
        name=CONTAINER_NAME,
        annotation=Container,
        kind=Parameter.KEYWORD_ONLY,
    )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda _, p: p[CONTAINER_NAME],
        additional_params=additional_params,
        is_async=True,
    )


class ContainerMiddleware(BaseMiddleware):
    def __init__(self, container):
        self.container = container

    async def __call__(
        self, handler, event, data,
    ):
        async with self.container({TelegramObject: event}) as sub_container:
            data[CONTAINER_NAME] = sub_container
            return await handler(event, data)


class AutoInjectMiddleware(BaseMiddleware):
    async def __call__(
        self, handler, event, data,
    ):
        old_handler: HandlerObject = data["handler"]
        if is_dishka_injected(old_handler.callback):
            return await handler(event, data)

        new_handler = HandlerObject(
            callback=inject(old_handler.callback),
            filters=old_handler.filters,
            flags=old_handler.flags,
        )
        old_handler.callback = new_handler.callback
        old_handler.params = new_handler.params
        old_handler.varkw = new_handler.varkw
        old_handler.awaitable = new_handler.awaitable
        return await handler(event, data)


def setup_dishka(
    container: AsyncContainer,
    router: Router,
    *,
    auto_inject: bool = False,
) -> None:
    middleware = ContainerMiddleware(container)
    auto_inject_middleware = AutoInjectMiddleware()

    for observer in router.observers.values():
        observer.outer_middleware(middleware)
        if auto_inject and observer.event_name != "update":
            observer.middleware(auto_inject_middleware)
