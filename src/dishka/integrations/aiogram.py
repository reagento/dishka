__all__ = [
    "Depends",
    "inject",
    "ContainerMiddleware",
    "setup_container",
]

from inspect import Parameter
from typing import Container

from aiogram import BaseMiddleware, Router
from aiogram.types import TelegramObject

from .base import Depends, wrap_injection
from .. import AsyncContainer


def inject(func):
    getter = lambda kwargs: kwargs["dishka_container"]
    additional_params = [Parameter(
        name="dishka_container",
        annotation=Container,
        kind=Parameter.KEYWORD_ONLY,
    )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=getter,
        additional_params=additional_params,
        is_async=True,
    )


class ContainerMiddleware(BaseMiddleware):
    def __init__(self, container):
        self.container = container

    async def __call__(
            self, handler, event, data,
    ):
        async with self.container({TelegramObject: event}) as subcontainer:
            data["dishka_container"] = subcontainer
            return await handler(event, data)


def setup_container(router: Router, container: AsyncContainer):
    middleware = ContainerMiddleware(container)
    for observer in router.observers.values():
        observer.middleware(middleware)
