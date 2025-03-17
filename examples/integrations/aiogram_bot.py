import asyncio
import logging
import os
import random
from collections.abc import AsyncIterator

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Chat, Message, TelegramObject, User

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.aiogram import (
    AiogramMiddlewareData,
    AiogramProvider,
    FromDishka,
    inject,
    setup_dishka,
)

# app dependency logic

class MyProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_int(self) -> AsyncIterator[int]:
        print("solve int")
        yield random.randint(0, 10000)

    @provide(scope=Scope.REQUEST)
    async def get_user(self, obj: TelegramObject) -> User:
        return obj.from_user

    @provide(scope=Scope.REQUEST)
    async def get_chat(self, middleware_data: AiogramMiddlewareData) -> Chat | None:
        return middleware_data.get("event_chat")


# app

API_TOKEN = os.getenv("BOT_TOKEN")
router = Router()


@router.message()
# If auto_inject=True is not passed, you need to manually apply the @inject decorator
#@inject
async def start(
    message: Message,
    user: FromDishka[User],
    value: FromDishka[int],
    chat: FromDishka[Chat | None],
):
    chat_name = chat.username if chat else None
    await message.answer(f"Hello, {value}, {chat_name}, {user.full_name}!")


async def main():
    # real main
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    container = make_async_container(
        MyProvider(),
        AiogramProvider(),
    )
    setup_dishka(container=container, router=dp, auto_inject=True)
    try:
        await dp.start_polling(bot)
    finally:
        await container.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
