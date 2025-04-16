from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import litestar
import pytest
from litestar import Request, get, websocket_listener
from litestar.contrib.htmx.request import HTMXRequest
from litestar.testing import AsyncTestClient

from dishka import make_async_container
from dishka.integrations.litestar import (
    DishkaPlugin,
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
async def dishka_app_via_setup(
        view,
        provider,
        request_class: type[Request] = Request,
) -> AsyncGenerator[AsyncTestClient]:
    app = litestar.Litestar(request_class=request_class, debug=True)
    app.register(get("/")(inject(view)))
    app.register(websocket_listener("/ws")(websocket_handler))
    container = make_async_container(provider)
    setup_dishka(container, app)
    async with AsyncTestClient(app) as client:
        yield client
    await container.close()

@asynccontextmanager
async def dishka_app_via_plugin(
        view,
        provider,
        request_class: type[Request] = Request,
) -> AsyncGenerator[AsyncTestClient]:
    container = make_async_container(provider)
    app = litestar.Litestar(request_class=request_class,
                            plugins=[DishkaPlugin(container=container)])
    app.register(get("/")(inject(view)))
    app.register(websocket_listener("/ws")(websocket_handler))
    async with AsyncTestClient(app) as client:
        yield client
    await container.close()



async def websocket_handler(data: str):
    pass


def get_with_app(request_class: type[Request]):
    async def handler(
            request: request_class,
            a: FromDishka[AppDep],
            mock: FromDishka[Mock],
    ) -> None:
        mock(a)

    return handler


def get_with_request(request_class: type[Request]):
    async def handler(
            request: request_class,
            a: FromDishka[RequestDep],
            mock: FromDishka[Mock],
    ) -> None:
        mock(a)

    return handler



@pytest.mark.parametrize("client_setup", [dishka_app_via_setup,
                                          dishka_app_via_plugin])
@pytest.mark.parametrize("request_class", [Request, HTMXRequest])
@pytest.mark.asyncio
async def test_app_dependency(request_class, app_provider: AppProvider,
                              client_setup: AsyncTestClient) -> None:
    async with client_setup(get_with_app(request_class),
                            app_provider) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


@pytest.mark.parametrize("client_setup", [dishka_app_via_setup,
                                          dishka_app_via_plugin])
@pytest.mark.parametrize("request_class", [Request, HTMXRequest])
@pytest.mark.asyncio
async def test_request_dependency(request_class, app_provider: AppProvider,
                                  client_setup: AsyncTestClient) -> None:
    async with client_setup(
            get_with_request(request_class),
            app_provider,
            request_class,
    ) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.parametrize("client_setup", [dishka_app_via_setup,
                                          dishka_app_via_plugin])
@pytest.mark.parametrize("request_class", [Request, HTMXRequest])
@pytest.mark.asyncio
async def test_request_dependency2(request_class, app_provider: AppProvider,
                                   client_setup: AsyncTestClient) -> None:
    async with client_setup(
            get_with_request(request_class),
            app_provider,
            request_class,
    ) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()
        await client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.parametrize("client_setup", [dishka_app_via_setup,
                                          dishka_app_via_plugin])
@pytest.mark.asyncio
async def test_request_middleware(app_provider: AppProvider,
                                  client_setup: AsyncTestClient) -> None:
    async with client_setup(
            get_with_request(Request),
            app_provider,
            Request,
    ) as client:
        with await client.websocket_connect("/ws") as websocket:
            websocket.send("test")
