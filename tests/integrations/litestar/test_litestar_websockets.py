from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from litestar import Litestar, websocket_listener
from litestar.handlers import WebsocketListener
from litestar.testing import TestClient

from dishka import make_async_container
from dishka.integrations.litestar import (
    DishkaRouter,
    FromDishka,
    inject_websocket,
    setup_dishka,
)
from ..common import (
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
    app = Litestar([view], debug=True)
    container = make_async_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield TestClient(app)
    await container.close()


@asynccontextmanager
async def dishka_auto_app(view, provider) -> AsyncGenerator[TestClient, None]:
    router = DishkaRouter("", route_handlers=[])
    router.register(view)
    app = Litestar([router], debug=True)
    container = make_async_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield TestClient(app)
    await container.close()


@websocket_listener("/")
@inject_websocket
async def get_with_app(
    data: str,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


@websocket_listener("/")
async def auto_get_with_app(
    data: str,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


class GetWithApp(WebsocketListener):
    path = "/"

    @inject_websocket
    async def on_receive(
        self,
        data: str,
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
    ) -> str:
        mock(a)
        return "passed"


class AutoGetWithApp(WebsocketListener):
    path = "/"

    async def on_receive(
        self,
        data: str,
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
    ) -> str:
        mock(a)
        return "passed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("app_factory", "view"),
    [
        (dishka_app, get_with_app),
        (dishka_auto_app, auto_get_with_app),
        (dishka_app, GetWithApp),
        (dishka_auto_app, AutoGetWithApp),
    ],
)
async def test_app_dependency(
    app_factory,
    view,
    ws_app_provider: WebSocketAppProvider,
):
    async with app_factory(view, ws_app_provider) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(APP_DEP_VALUE)
        ws_app_provider.app_released.assert_not_called()
    ws_app_provider.app_released.assert_called()


@websocket_listener("/")
@inject_websocket
async def get_with_request(
    data: str,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


@websocket_listener("/")
async def auto_get_with_request(
    data: str,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


class GetWithRequest(WebsocketListener):
    path = "/"

    @inject_websocket
    async def on_receive(
        self,
        data: str,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
    ) -> str:
        mock(a)
        return "passed"


class AutoGetWithRequest(WebsocketListener):
    path = "/"

    async def on_receive(
        self,
        data: str,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
    ) -> str:
        mock(a)
        return "passed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("app_factory", "view"),
    [
        (dishka_app, get_with_request),
        (dishka_auto_app, auto_get_with_request),
        (dishka_app, GetWithRequest),
        (dishka_auto_app, AutoGetWithRequest),
    ],
)
async def test_request_dependency(
    app_factory,
    view,
    ws_app_provider: WebSocketAppProvider,
):
    async with app_factory(view, ws_app_provider) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"
        ws_app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        ws_app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("app_factory", "view"),
    [
        (dishka_app, get_with_request),
        (dishka_auto_app, auto_get_with_request),
        (dishka_app, GetWithRequest),
        (dishka_auto_app, AutoGetWithRequest),
    ],
)
async def test_request_dependency2(
    app_factory,
    view,
    ws_app_provider: WebSocketAppProvider,
):
    async with app_factory(view, ws_app_provider) as client:
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


@websocket_listener("/")
@inject_websocket
async def get_with_websocket(
    data: str,
    ws: FromDishka[WebSocketDep],
    mock: FromDishka[Mock],
) -> str:
    mock(ws)
    return "passed"


@websocket_listener("/")
async def auto_get_with_websocket(
    data: str,
    ws: FromDishka[WebSocketDep],
    mock: FromDishka[Mock],
) -> str:
    mock(ws)
    return "passed"


class GetWithWebsocket(WebsocketListener):
    path = "/"

    @inject_websocket
    async def on_receive(
        self,
        data: str,
        a: FromDishka[WebSocketDep],
        mock: FromDishka[Mock],
    ) -> str:
        mock(a)
        return "passed"


class AutoGetWithWebsocket(WebsocketListener):
    path = "/"

    async def on_receive(
        self,
        data: str,
        ws: FromDishka[WebSocketDep],
        mock: FromDishka[Mock],
    ) -> str:
        mock(ws)
        return "passed"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("app_factory", "view"),
    [
        (dishka_app, get_with_websocket),
        (dishka_auto_app, auto_get_with_websocket),
        (dishka_app, GetWithWebsocket),
        (dishka_auto_app, AutoGetWithWebsocket),
    ],
)
async def test_websocket_dependency(
    app_factory,
    view,
    ws_app_provider: WebSocketAppProvider,
):
    async with app_factory(view, ws_app_provider) as client:
        with client.websocket_connect("/") as connection:
            connection.send_text("...")
            assert connection.receive_text() == "passed"

        ws_app_provider.mock.assert_called_with(WS_DEP_VALUE)
        ws_app_provider.websocket_released.assert_called_once()
