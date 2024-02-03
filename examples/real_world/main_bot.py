import asyncio
import logging
import os

from aiogram import Bot, Dispatcher

from dishka.integrations.aiogram import setup_dishka
from myapp.ioc import AdaptersProvider, InteractorProvider
from myapp.presentation_bot import router


async def main():
    # real main
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()
    dp.include_router(router)
    setup_dishka(
        providers=[InteractorProvider(), AdaptersProvider()],
        router=dp,
    )
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
