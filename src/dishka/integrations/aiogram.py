__all__ = [
    "Depends",
    "inject",
    "setup_dishka",
]

from inspect import Parameter
from typing import Container

from aiogram import BaseMiddleware, Router
from aiogram.types import TelegramObject

from dishka import AsyncContainer
from .base import Depends, wrap_injection

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


def setup_dishka(container: AsyncContainer, router: Router) -> None:
    middleware = ContainerMiddleware(container)
    for observer in router.observers.values():
        observer.middleware(middleware)
