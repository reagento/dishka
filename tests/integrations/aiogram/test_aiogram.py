from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated
from unittest.mock import Mock

import pytest
from aiogram import Dispatcher
from aiogram.types import Chat, Message, Update, User

from dishka import make_async_container
from dishka.integrations.aiogram import Depends, inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


@asynccontextmanager
async def dishka_app(handler, provider):
    dp = Dispatcher()
    dp.message()(inject(handler))
    container = make_async_container(provider)
    setup_dishka(container, router=dp)

    await dp.emit_startup()
    yield dp
    await dp.emit_shutdown()
    await container.close()


async def send_message(bot, dp):
    await dp.feed_update(bot, Update(
        update_id=1,
        message=Message(
            message_id=2,
            date=datetime.fromtimestamp(1234567890),
            chat=Chat(id=1, type="private"),
            from_user=User(
                id=1, is_bot=False,
                first_name="User",
            ),
            text="/start",
        ),
    ))


async def handle_with_app(
        _: Message,
        a: Annotated[AppDep, Depends()],
        mock: Annotated[Mock, Depends()],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_app_dependency(bot, app_provider: AppProvider):
    async with dishka_app(handle_with_app, app_provider) as dp:
        await send_message(bot, dp)
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()

    app_provider.app_released.assert_called()


async def handle_with_request(
        _: Message,
        a: Annotated[RequestDep, Depends()],
        mock: Annotated[Mock, Depends()],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_request_dependency(bot, app_provider: AppProvider):
    async with dishka_app(handle_with_request, app_provider) as dp:
        await send_message(bot, dp)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_request_dependency2(bot, app_provider: AppProvider):
    async with dishka_app(handle_with_request, app_provider) as dp:
        await send_message(bot, dp)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()
        await send_message(bot, dp)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
