import asyncio
import logging
import os
import random
from inspect import Parameter
from typing import Annotated, Container, Iterable

from aiogram import BaseMiddleware, Bot, Dispatcher, Router
from aiogram.types import Message, TelegramObject, User

from dishka import Provider, Scope, make_async_container, provide
from dishka.inject import Depends, wrap_injection


# framework level
def inject(func):
    getter = lambda kwargs: kwargs["container"]
    additional_params = [Parameter(
        name="container",
        annotation=Container,
        kind=Parameter.KEYWORD_ONLY,
    )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=getter,
        additional_params=additional_params,
        is_async=True,
    )


class ContainerMiddleware(BaseMiddleware):
    def __init__(self, container):
        self.container = container

    async def __call__(
            self, handler, event, data,
    ):
        async with self.container({TelegramObject: event}) as subcontainer:
            data["container"] = subcontainer
            return await handler(event, data)


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
    async with make_async_container(MyProvider()) as container:
        bot = Bot(token=API_TOKEN)
        dp = Dispatcher()
        for observer in dp.observers.values():
            observer.middleware(ContainerMiddleware(container))
        dp.include_router(router)

        await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
