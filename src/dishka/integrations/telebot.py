__all__ = [
    "Depends",
    "inject",
    "setup_dishka",
]

from inspect import Parameter
from typing import Sequence

import telebot
from telebot import BaseMiddleware, TeleBot

from dishka import Container, Provider, make_container
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
        is_async=False,
    )


class ContainerMiddleware(BaseMiddleware):
    update_types = telebot.util.update_types

    def __init__(self, container):
        super().__init__()
        self.container = container

    def pre_process(self, message, data):
        dishka_container_wrapper = self.container({type(message): message})
        data["dishka_container_wrapper"] = dishka_container_wrapper
        data["dishka_container"] = dishka_container_wrapper.__enter__()

    def post_process(self, message, data, exception):
        data["dishka_container_wrapper"].__exit__(None, None, None)


def setup_dishka(providers: Sequence[Provider], bot: TeleBot) -> Container:
    container_wrapper = make_container(*providers)
    container = container_wrapper.__enter__()
    middleware = ContainerMiddleware(container)
    bot.setup_middleware(middleware)
    return container
