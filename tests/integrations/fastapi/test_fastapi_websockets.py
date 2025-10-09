from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from fastapi import FastAPI, WebSocket
from fastapi.routing import APIWebSocketRoute
from fastapi.testclient import TestClient

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import (
    FromDishka,
    inject,
    setup_dishka,
)
from tests.integrations.common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    WS_DEP_VALUE,
    AppDep,
    RequestDep,
    WebSocketAppProvider,
    WebSocketDep,
)


@asynccontextmanager
async def dishka_app(view, provider) -> AsyncGenerator[TestClient, None]:
    app = FastAPI(routes=[APIWebSocketRoute("/", inject(view))])
    container = make_async_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield TestClient(app)
    await container.close()


async def get_with_app(
    websocket: WebSocket,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    await websocket.accept()
    await websocket.receive()
    mock(a)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_app_dependency(ws_app_provider: WebSocketAppProvider):
    async with dishka_app(get_with_app, ws_app_provider) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(APP_DEP_VALUE)
        ws_app_provider.app_released.assert_not_called()
    ws_app_provider.app_released.assert_called()


async def get_with_request(
    websocket: WebSocket,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    await websocket.accept()
    await websocket.receive()
    mock(a)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_request_dependency(ws_app_provider: WebSocketAppProvider):
    async with dishka_app(get_with_request, ws_app_provider) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"
        ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_request_dependency2(ws_app_provider: WebSocketAppProvider):
    async with dishka_app(get_with_request, ws_app_provider) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.request_released.assert_called_once()
        ws_app_provider.request_released.reset_mock()

        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


async def get_with_websocket(
    websocket: WebSocket,
    ws: FromDishka[WebSocketDep],
    mock: FromDishka[Mock],
) -> None:
    await websocket.accept()
    await websocket.receive()
    mock(ws)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_websocket_dependency(ws_app_provider: WebSocketAppProvider):
    async with dishka_app(get_with_websocket, ws_app_provider) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(WS_DEP_VALUE)
        ws_app_provider.websocket_released.assert_called_once()


async def get_without_websocket_param(
    a: FromDishka[AppDep],
    container: FromDishka[AsyncContainer],
    mock: FromDishka[Mock],
) -> None:
    websocket = await container.get(WebSocket)
    await websocket.accept()
    await websocket.receive()
    mock(a)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_without_websocket_param_app_dep(
    ws_app_provider: WebSocketAppProvider,
):
    async with dishka_app(
        get_without_websocket_param,
        ws_app_provider,
    ) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(APP_DEP_VALUE)
        ws_app_provider.app_released.assert_not_called()
    ws_app_provider.app_released.assert_called()


async def get_without_websocket_param_request(
    a: FromDishka[RequestDep],
    container: FromDishka[AsyncContainer],
    mock: FromDishka[Mock],
) -> None:
    websocket = await container.get(WebSocket)
    await websocket.accept()
    await websocket.receive()
    mock(a)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_without_websocket_param_request_dep(
    ws_app_provider: WebSocketAppProvider,
):
    async with dishka_app(
        get_without_websocket_param_request,
        ws_app_provider,
    ) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


async def get_without_websocket_param_ws_dep(
    ws: FromDishka[WebSocketDep],
    container: FromDishka[AsyncContainer],
    mock: FromDishka[Mock],
) -> None:
    websocket = await container.get(WebSocket)
    await websocket.accept()
    await websocket.receive()
    mock(ws)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_without_websocket_param_ws_dep(
    ws_app_provider: WebSocketAppProvider,
):
    async with dishka_app(
        get_without_websocket_param_ws_dep,
        ws_app_provider,
    ) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(WS_DEP_VALUE)
        ws_app_provider.websocket_released.assert_called_once()


async def get_with_dishka_websocket(
    websocket: FromDishka[WebSocket],
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    await websocket.accept()
    await websocket.receive()
    mock(a)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_with_dishka_websocket_app_dep(
    ws_app_provider: WebSocketAppProvider,
):
    async with dishka_app(
        get_with_dishka_websocket,
        ws_app_provider,
    ) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(APP_DEP_VALUE)
        ws_app_provider.app_released.assert_not_called()
    ws_app_provider.app_released.assert_called()


async def get_with_dishka_websocket_request(
    websocket: FromDishka[WebSocket],
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    await websocket.accept()
    await websocket.receive()
    mock(a)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_with_dishka_websocket_request_dep(
    ws_app_provider: WebSocketAppProvider,
):
    async with dishka_app(
        get_with_dishka_websocket_request,
        ws_app_provider,
    ) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


async def get_with_dishka_websocket_ws_dep(
    websocket: FromDishka[WebSocket],
    ws: FromDishka[WebSocketDep],
    mock: FromDishka[Mock],
) -> None:
    await websocket.accept()
    await websocket.receive()
    mock(ws)
    await websocket.send_text("passed")


@pytest.mark.asyncio
async def test_with_dishka_websocket_ws_dep(
    ws_app_provider: WebSocketAppProvider,
):
    async with dishka_app(
        get_with_dishka_websocket_ws_dep,
        ws_app_provider,
    ) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(WS_DEP_VALUE)
        ws_app_provider.websocket_released.assert_called_once()
