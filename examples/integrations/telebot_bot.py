import logging
import os
import random
from collections.abc import Iterable

import telebot
from telebot.types import Message

from dishka import Provider, Scope, make_container, provide
from dishka.integrations.telebot import (
    FromDishka,
    TelebotProvider,
    inject,
    setup_dishka,
)


# app dependency logic
class MyProvider(Provider):
    @provide(scope=Scope.APP)
    def get_int(self) -> Iterable[int]:
        print("solve int")
        yield random.randint(0, 10000)


# app
API_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(API_TOKEN, use_class_middlewares=True)


@bot.message_handler()
@inject
def start(
        message: Message,
        value: FromDishka[int],
):
    bot.reply_to(message, f"Hello, {value}!")


logging.basicConfig(level=logging.INFO)

container = make_container(MyProvider(), TelebotProvider())
setup_dishka(container=container, bot=bot)
try:
    bot.infinity_polling()
finally:
    container.close()
