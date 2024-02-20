import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from myapp.ioc import AdaptersProvider, InteractorProvider
from myapp.presentation_bot import router

from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka


async def main():
    # real main
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    container = make_async_container(AdaptersProvider(), InteractorProvider())
    setup_dishka(container=container, router=dp)
    try:
        await dp.start_polling(bot)
    finally:
        await container.close()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
