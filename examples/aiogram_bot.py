import asyncio
import logging
import os
import random
from collections.abc import AsyncIterator
from typing import Annotated

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, TelegramObject, User

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.aiogram import FromDishka, inject, setup_dishka

# app dependency logic

class MyProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> AsyncIterator[Dispatcher]:
        print("solve int")
        yield random.randint(0, 10000)

    @provide(scope=Scope.REQUEST)
    async def get_name(self, request: TelegramObject) -> User:
        return request.from_user


# app

API_TOKEN = os.getenv("BOT_TOKEN")
router = Router()


@router.message()
# if auto_inject=True is specified in the setup_dishka, then you do not need to specify a decorator
@inject
async def start(
    message: Message,
    user: Annotated[User, FromDishka()],
    value: Annotated[int, FromDishka()],
):
    await message.answer(f"Hello, {1}, {user.full_name}!")


async def main():
    # real main
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    container = make_async_container(MyProvider())
    setup_dishka(container=container, router=dp)
    try:
        await dp.start_polling(bot)
    finally:
        await container.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
