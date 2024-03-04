from contextlib import asynccontextmanager
from typing import Annotated, Type
from unittest.mock import Mock

import litestar
import pytest
from asgi_lifespan import LifespanManager
from litestar import get, Request
from litestar.contrib.htmx.request import HTMXRequest
from litestar.testing import TestClient

from dishka import make_async_container
from dishka.integrations.litestar import (
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
async def dishka_app(view, provider, request_class: Type[Request] = Request) -> TestClient:
    app = litestar.Litestar(request_class=request_class)
    app.register(get("/")(inject(view)))
    container = make_async_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield litestar.testing.TestClient(app)
    await container.close()


async def get_with_app(
        a: Annotated[AppDep, FromDishka()],
        mock: Annotated[Mock, FromDishka()],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider):
    async with dishka_app(get_with_app, app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def get_handler(request_class: type[Request]):
    async def get_with_request(
            request: request_class,
            a: Annotated[RequestDep, FromDishka()],
            mock: Annotated[Mock, FromDishka()],
    ) -> None:
        mock(a)

    return get_with_request


@pytest.mark.parametrize("request_class", [Request, HTMXRequest])
@pytest.mark.asyncio
async def test_request_dependency(request_class, app_provider: AppProvider):
    async with dishka_app(get_handler(request_class), app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_request_dependency2(app_provider: AppProvider):
    async with dishka_app(get_handler(), app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()
        client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
