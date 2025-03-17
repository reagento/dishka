from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from aiohttp.test_utils import TestClient, TestServer
from aiohttp.web_app import Application
from rapidy import Rapidy
from rapidy.http import Request, get
from rapidy.typedefs import Handler

from dishka import make_async_container
from dishka.integrations.rapidy import FromDishka, inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


async def get_with_app(
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


async def get_with_request(
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


@asynccontextmanager
async def dishka_app(
        handler: Handler,
        provider: AppProvider,
) -> AsyncGenerator[TestClient[Request, Application], None]:
    rapidy = Rapidy(http_route_handlers=[get("/")(inject(handler))])

    container = make_async_container(provider)
    setup_dishka(container, app=rapidy)

    async with (
        TestServer(rapidy) as server,
        TestClient(server) as client,
    ):
        yield client

    await container.close()


@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider):
    async with dishka_app(
            handler=get_with_app,
            provider=app_provider,
    ) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


@pytest.mark.asyncio
async def test_request_dependency(app_provider: AppProvider):
    async with dishka_app(get_with_request, app_provider) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_request_dependency_ext(app_provider: AppProvider):
    async with dishka_app(get_with_request, app_provider) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()

        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
