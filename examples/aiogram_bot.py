import asyncio
import logging
import os
import random
from typing import Annotated, Iterable

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message, TelegramObject, User

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.aiogram import Depends, inject, setup_container


# app dependency logic

class MyProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> Iterable[int]:
        print("solve int")
        yield random.randint(0, 10000)

    @provide(scope=Scope.REQUEST)
    async def get_name(self, request: TelegramObject) -> User:
        return request.from_user


# app
API_TOKEN = os.getenv("BOT_TOKEN")
router = Router()


@router.message()
@inject
async def start(
        message: Message,
        user: Annotated[User, Depends()],
        value: Annotated[int, Depends()],
):
    await message.answer(f"Hello, {value}, {user.full_name}!")


async def main():
    # real main
    logging.basicConfig(level=logging.INFO)
    async with make_async_container(MyProvider(), with_lock=True) as container:
        bot = Bot(token=API_TOKEN)
        dp = Dispatcher()
        dp.include_router(router)
        setup_container(dp, container)
        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
