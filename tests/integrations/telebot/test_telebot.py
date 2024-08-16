from contextlib import contextmanager
from unittest.mock import Mock

from telebot import TeleBot
from telebot.types import Message, Update

from dishka import make_container
from dishka.integrations.telebot import FromDishka, inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


@contextmanager
def dishka_app(handler, provider):
    bot = TeleBot(
        "1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        use_class_middlewares=True,
        threaded=False,
    )
    bot.message_handler()(inject(handler))
    container = make_container(provider)
    setup_dishka(container=container, bot=bot)
    yield bot
    container.close()


def send_message(bot: TeleBot):
    update = Update.de_json({
        "update_id": 1,
        "message": {
            "chat": {"id": 1, "type": "private"},
            "message_id": 2,
            "date": 1234567890,
            "text": "/start",
        },
    })
    bot.process_new_updates([update])


def handle_with_app(
        _: Message,
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


def test_app_dependency(app_provider: AppProvider):
    with dishka_app(handle_with_app, app_provider) as bot:
        send_message(bot)
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def handle_with_request(
        _: Message,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


def test_request_dependency(app_provider: AppProvider):
    with dishka_app(handle_with_request, app_provider) as bot:
        send_message(bot)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def test_request_dependency2(app_provider: AppProvider):
    with dishka_app(handle_with_request, app_provider) as bot:
        send_message(bot)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()
        send_message(bot)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
