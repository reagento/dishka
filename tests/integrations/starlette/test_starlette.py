from contextlib import asynccontextmanager
from typing import Annotated
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from dishka.integrations.starlette import (
    Depends,
    DishkaApp,
    inject,
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
    app = Starlette(routes=[Route("/", inject(view), methods=["GET"])])
    app = DishkaApp(
        providers=[provider],
        app=app,
    )
    async with LifespanManager(app):
        yield TestClient(app)


async def get_with_app(
        _: Request,
        a: Annotated[AppDep, Depends()],
        mock: Annotated[Mock, Depends()],
) -> PlainTextResponse:
    mock(a)
    return PlainTextResponse("passed")


@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider):
    async with dishka_app(get_with_app, app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


async def get_with_request(
        _: Request,
        a: Annotated[RequestDep, Depends()],
        mock: Annotated[Mock, Depends()],
) -> PlainTextResponse:
    mock(a)
    return PlainTextResponse("passed")


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
