from contextlib import asynccontextmanager
from typing import Annotated
from unittest.mock import Mock

import litestar
import pytest
from asgi_lifespan import LifespanManager
from litestar import get
from litestar.testing import TestClient

from dishka import make_async_container
from dishka.integrations.litestar import (
    Depends,
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
async def dishka_app(view, provider) -> TestClient:
    app = litestar.Litestar()
    app.register(get("/")(inject(view)))
    container = make_async_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield litestar.testing.TestClient(app)
    await container.close()


async def get_with_app(
    a: Annotated[AppDep, Depends()],
    mock: Annotated[Mock, Depends()],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider):
    async with dishka_app(get_with_app, app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


async def get_with_request(
    a: Annotated[RequestDep, Depends()],
    mock: Annotated[Mock, Depends()],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_request_dependency(app_provider: AppProvider):
    async with dishka_app(get_with_request, app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_request_dependency2(app_provider: AppProvider):
    async with dishka_app(get_with_request, app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()
        client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
