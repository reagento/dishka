__all__ = [
    "Depends",
    "inject",
    "setup_dishka",
]

from inspect import Parameter
from typing import Container, Sequence

from aiogram import BaseMiddleware, Router
from aiogram.types import TelegramObject

from dishka import Provider, make_async_container
from .base import Depends, wrap_injection


def inject(func):
    additional_params = [Parameter(
        name="dishka_container",
        annotation=Container,
        kind=Parameter.KEYWORD_ONLY,
    )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda _, p: p["dishka_container"],
        additional_params=additional_params,
        is_async=True,
    )


class ContainerMiddleware(BaseMiddleware):
    def __init__(self, container_wrapper):
        self.container_wrapper = container_wrapper
        self.container = None

    async def __call__(
            self, handler, event, data,
    ):
        async with self.container({TelegramObject: event}) as subcontainer:
            data["dishka_container"] = subcontainer
            return await handler(event, data)

    async def startup(self):
        self.container = await self.container_wrapper.__aenter__()

    async def shutdown(self):
        await self.container_wrapper.__aexit__(None, None, None)


def setup_dishka(providers: Sequence[Provider], router: Router) -> None:
    middleware = ContainerMiddleware(make_async_container(*providers))

    router.startup()(middleware.startup)
    router.shutdown()(middleware.shutdown)

    for observer in router.observers.values():
        observer.middleware(middleware)
