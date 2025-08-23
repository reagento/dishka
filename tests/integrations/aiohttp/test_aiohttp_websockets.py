from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from aiohttp.test_utils import TestClient, TestServer
from aiohttp.web import WebSocketResponse
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from aiohttp.web_routedef import RouteTableDef

from dishka import make_async_container
from dishka.integrations.aiohttp import (
    FromDishka,
    inject,
    setup_dishka,
)
from tests.integrations.aiohttp.conftest import custom_inject
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    WS_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
    WebSocketDep,
)


@asynccontextmanager
async def dishka_app(view, provider) -> AsyncGenerator[TestClient, None]:
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
async def dishka_auto_app(view, provider) -> AsyncGenerator[TestClient, None]:
    app = Application()

    app.router.add_get("/", view)

    container = make_async_container(provider)
    setup_dishka(container, app=app, auto_inject=True)
    client = TestClient(TestServer(app))
    await client.start_server()
    yield client
    await client.close()
    await container.close()


@asynccontextmanager
async def dishka_custom_auto_inject_app(
    view,
    provider,
) -> AsyncGenerator[TestClient, None]:
    app = Application()

    app.router.add_get("/", view)

    container = make_async_container(provider)
    setup_dishka(container, app=app, auto_inject=custom_inject)
    client = TestClient(TestServer(app))
    await client.start_server()
    yield client
    await client.close()
    await container.close()


async def get_with_app(
    request: Request,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> WebSocketResponse:
    websocket = WebSocketResponse()
    await websocket.prepare(request)

    await websocket.receive()
    mock(a)
    await websocket.send_str("passed")
    return websocket


@pytest.mark.parametrize(
    "app_factory",
    [
        dishka_app,
        dishka_auto_app,
    ],
)
@pytest.mark.asyncio
async def test_app_dependency(
    ws_app_provider: AppProvider,
    app_factory,
):
    async with app_factory(get_with_app, ws_app_provider) as client:
        async with client.ws_connect("/") as conn:
            await conn.send_str("...")
            assert await conn.receive_str() == "passed"
        ws_app_provider.mock.assert_called_with(APP_DEP_VALUE)
        ws_app_provider.app_released.assert_not_called()
    ws_app_provider.app_released.assert_called()


async def get_with_request(
    request: Request,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> WebSocketResponse:
    websocket = WebSocketResponse()
    await websocket.prepare(request)

    await websocket.receive()
    mock(a)
    await websocket.send_str("passed")
    return websocket


@pytest.mark.parametrize(
    "app_factory",
    [
        dishka_app,
        dishka_auto_app,
    ],
)
@pytest.mark.asyncio
async def test_request_dependency(ws_app_provider: AppProvider, app_factory):
    async with app_factory(get_with_request, ws_app_provider) as client:
        async with client.ws_connect("/") as conn:
            await conn.send_str("...")
            assert await conn.receive_str() == "passed"

        ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


@pytest.mark.parametrize(
    "app_factory",
    [
        dishka_app,
        dishka_auto_app,
    ],
)
@pytest.mark.asyncio
async def test_request_dependency2(ws_app_provider: AppProvider, app_factory):
    async with app_factory(get_with_request, ws_app_provider) as client:
        async with client.ws_connect("/") as conn:
            await conn.send_str("...")
            assert await conn.receive_str() == "passed"

        ws_app_provider.request_released.assert_called_once()
        ws_app_provider.request_released.reset_mock()

        async with client.ws_connect("/") as conn:
            await conn.send_str("...")
            assert await conn.receive_str() == "passed"

        ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


async def get_with_websocket(
    request: Request,
    ws: FromDishka[WebSocketDep],
    mock: FromDishka[Mock],
) -> None:
    websocket = WebSocketResponse()
    await websocket.prepare(request)

    await websocket.receive()
    mock(ws)
    await websocket.send_str("passed")
    return websocket


@pytest.mark.parametrize(
    "app_factory",
    [
        dishka_app,
        dishka_auto_app,
    ],
)
@pytest.mark.asyncio
async def test_websocket_dependency(ws_app_provider: AppProvider, app_factory):
    async with app_factory(get_with_websocket, ws_app_provider) as client:
        async with client.ws_connect("/") as conn:
            await conn.send_str("...")
            assert await conn.receive_str() == "passed"

        ws_app_provider.mock.assert_called_with(WS_DEP_VALUE)
        ws_app_provider.websocket_released.assert_called_once()


async def handle_for_custom_auto_inject(
    request: Request,
    ws: FromDishka[WebSocketDep],
    mock: FromDishka[Mock],
) -> None:
    pass


@pytest.mark.asyncio
async def test_custom_auto_inject(ws_app_provider: AppProvider):
    async with dishka_custom_auto_inject_app(
        handle_for_custom_auto_inject,
        ws_app_provider,
    ):
        assert getattr(handle_for_custom_auto_inject, "__custom__", False)
