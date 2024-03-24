__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from inspect import Parameter

import telebot
from telebot import BaseMiddleware, TeleBot

from dishka import Container, FromDishka
from .base import wrap_injection

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
        is_async=False,
    )


class ContainerMiddleware(BaseMiddleware):
    update_types = telebot.util.update_types

    def __init__(self, container):
        super().__init__()
        self.container = container

    def pre_process(self, message, data):
        dishka_container_wrapper = self.container({type(message): message})
        data[CONTAINER_NAME + "_wrapper"] = dishka_container_wrapper
        data[CONTAINER_NAME] = dishka_container_wrapper.__enter__()

    def post_process(self, message, data, exception):
        data[CONTAINER_NAME + "_wrapper"].__exit__(None, None, None)


def setup_dishka(container: Container, bot: TeleBot) -> Container:
    middleware = ContainerMiddleware(container)
    bot.setup_middleware(middleware)
    return container
