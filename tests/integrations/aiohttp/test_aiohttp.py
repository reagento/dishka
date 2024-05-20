from collections.abc import AsyncIterable
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from aiohttp.test_utils import TestClient, TestServer
from aiohttp.web_app import Application
from aiohttp.web_response import Response
from aiohttp.web_routedef import RouteTableDef

from dishka import make_async_container
from dishka.integrations.aiohttp import (
    FromDishka,
    inject,
    setup_dishka,
)
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


@asynccontextmanager
async def dishka_app(view, provider) -> AsyncIterable[TestClient]:
    app = Application()

    router = RouteTableDef()
    router.get("/")(inject(view))

    app.add_routes(router)
    container = make_async_container(provider)
    setup_dishka(container, app=app)
    client = TestClient(TestServer(app))
    await client.start_server()
    yield client
    await client.close()
    await container.close()


@asynccontextmanager
async def dishka_auto_app(view, provider) -> AsyncIterable[TestClient]:
    app = Application()

    app.router.add_get("/", view)

    container = make_async_container(provider)
    setup_dishka(container, app=app, auto_inject=True)
    client = TestClient(TestServer(app))
    await client.start_server()
    yield client
    await client.close()
    await container.close()


async def get_with_app(
        _,
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
) -> Response:
    mock(a)
    return Response(text="passed")


@pytest.mark.parametrize("app_factory", [
    dishka_app, dishka_auto_app,
])
@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider, app_factory):
    async with app_factory(get_with_app, app_provider) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


async def get_with_request(
        _,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
) -> Response:
    mock(a)
    return Response(text="passed")


@pytest.mark.parametrize("app_factory", [
    dishka_app, dishka_auto_app,
])
@pytest.mark.asyncio
async def test_request_dependency(app_provider: AppProvider, app_factory):
    async with app_factory(get_with_request, app_provider) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.parametrize("app_factory", [
    dishka_app, dishka_auto_app,
])
@pytest.mark.asyncio
async def test_request_dependency2(app_provider: AppProvider, app_factory):
    async with app_factory(get_with_request, app_provider) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()
        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
