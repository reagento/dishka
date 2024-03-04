__all__ = [
    "Depends",
    "AutoInjectMiddleware",
    "FromDishka",
    "inject",
    "setup_dishka",
]
from collections.abc import Container
from inspect import Parameter
from typing import Annotated, get_origin

from aiogram import BaseMiddleware, Router
from aiogram.types import TelegramObject

from dishka import AsyncContainer, FromDishka
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


class AutoInjectMiddleware(BaseMiddleware):
    @staticmethod
    def _analysis_params(func) -> set[str]:
        new_params = [CONTAINER_NAME]
        for key, type_hint in func.__annotations__.items():
            if get_origin(type_hint) != Annotated:
                new_params.append(key)
        return set(new_params)

    async def __call__(
        self, handler, event, data,
    ):
        old_handler = data["handler"]
        if hasattr(old_handler.callback, "__dishka_injected__"):
            return await handler(event, data)

        new_handler = inject(old_handler.callback)
        old_handler.params = self._analysis_params(old_handler.callback)
        old_handler.callback = new_handler
        return await handler(event, data)


def setup_dishka(
    container: AsyncContainer,
    router: Router,
    auto_inject: bool | None = None,
) -> None:
    middleware = ContainerMiddleware(container)
    auto_inject_middleware = AutoInjectMiddleware()

    for observer in router.observers.values():
        observer.middleware(middleware)
        if auto_inject and observer.event_name != "update":
            observer.middleware(auto_inject_middleware)
