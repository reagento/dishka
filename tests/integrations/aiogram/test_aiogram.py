from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.event.handler import HandlerObject
from aiogram.types import Chat, Message, TelegramObject, Update, User

from dishka import AsyncContainer, make_async_container
from dishka.integrations.aiogram import (
    AiogramMiddlewareData,
    AiogramProvider,
    AutoInjectMiddleware,
    FromDishka,
    inject,
    setup_dishka,
)
from dishka.integrations.base import is_dishka_injected
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


@asynccontextmanager
async def dishka_early_inject_app(handler, provider):
    dp = Dispatcher()

    # first apply auto_inject
    container = make_async_container(provider)
    setup_dishka(container, router=dp, auto_inject=True)

    # then register raw handler
    dp.message.register(handler)

    await dp.emit_startup()
    yield dp
    await dp.emit_shutdown()
    await container.close()


@asynccontextmanager
async def dishka_auto_app(handler, provider):
    dp = Dispatcher()
    dp.message()(handler)
    container = make_async_container(provider)
    setup_dishka(container, router=dp, auto_inject=True)

    await dp.emit_startup()
    yield dp
    await dp.emit_shutdown()
    await container.close()


async def send_message(bot, dp):
    await dp.feed_update(bot, Update(
        update_id=1,
        message=Message(
            message_id=2,
            date=datetime.fromtimestamp(1234567890, tz=timezone.utc),
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
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.parametrize("app_factory", [
    dishka_app, dishka_auto_app,
])
@pytest.mark.asyncio
async def test_app_dependency(bot, app_provider: AppProvider, app_factory):
    async with app_factory(handle_with_app, app_provider) as dp:
        await send_message(bot, dp)
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()

    app_provider.app_released.assert_called()


async def handle_with_request(
        _: Message,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
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


async def handle_get_async_container(
        _: Message,
        dishka_container: AsyncContainer,
) -> None:
    assert isinstance(dishka_container, AsyncContainer)


@pytest.mark.asyncio
async def test_get_async_container(bot, app_provider: AppProvider):
    async with dishka_app(handle_get_async_container, app_provider) as dp:
        await send_message(bot, dp)


@pytest.mark.asyncio
async def test_early_autoinject(bot, app_provider: AppProvider):
    async with dishka_early_inject_app(
        handler=handle_with_request,
        provider=app_provider,
    ) as dp:
        await send_message(bot, dp)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_double_inject(bot, app_provider: AppProvider):
    """Apply auto_inject for already injected handler."""
    injected_handler = inject(handle_with_request)
    assert is_dishka_injected(injected_handler)

    async with dishka_auto_app(
        handler=injected_handler,
        provider=app_provider,
    ) as dp:
        await send_message(bot, dp)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.parametrize(
    "handler",
    [
        pytest.param(handle_with_request, id="raw-handler"),
        pytest.param(inject(handle_with_request), id="injected"),
    ],
)
@pytest.mark.asyncio
async def test_autoinject_middleware(
        bot: Bot,
        app_provider: AppProvider,
        handler: Callable,
):
    original_filters = []
    original_flags = {}

    handler_object = AsyncMock(HandlerObject)
    handler_object.callback = handler
    handler_object.filters = original_filters
    handler_object.flags = original_flags

    middleware = AutoInjectMiddleware()
    await middleware(
        handler=handler_object,
        event=Mock(TelegramObject),
        data={"handler": handler_object},
    )

    assert is_dishka_injected(handler_object.callback)
    assert handler_object.filters is original_filters
    assert handler_object.flags is original_flags


@pytest.mark.asyncio
async def test_aiogram_provider_with_container_middleware(bot):
    async def handler(
            message: Message,
            event: FromDishka[TelegramObject],
            middleware_data: FromDishka[AiogramMiddlewareData],
    ) -> None:
        assert event is message

        assert "bot" in middleware_data
        # disable_fsm=False - tests this keys
        assert "state" in middleware_data
        assert "raw_state" in middleware_data
        assert "fsm_storage" in middleware_data

    async with dishka_auto_app(handler, AiogramProvider()) as dp:
        await send_message(bot, dp)
