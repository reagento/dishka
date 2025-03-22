from contextlib import asynccontextmanager
from typing import Annotated
from unittest.mock import Mock

import fastapi
import pytest
from asgi_lifespan import LifespanManager
from fastapi.testclient import TestClient

from dishka import make_container
from dishka.integrations.fastapi import (
    DishkaSyncRoute,
    FromDishka,
    inject_sync,
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
    router = fastapi.APIRouter()
    router.get("/")(inject_sync(view))
    app = fastapi.FastAPI()
    app.include_router(router)
    container = make_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield fastapi.testclient.TestClient(app)
    container.close()


@asynccontextmanager
async def dishka_auto_app(view, provider) -> TestClient:
    router = fastapi.APIRouter(route_class=DishkaSyncRoute)
    router.get("/")(view)
    app = fastapi.FastAPI()
    app.include_router(router)
    container = make_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield fastapi.testclient.TestClient(app)
    container.close()


def get_with_app(
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.parametrize("app_factory", [
    dishka_app, dishka_auto_app,
])
@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider, app_factory):
    async with app_factory(get_with_app, app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def get_with_request(
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_request_dependency(app_provider: AppProvider):
    async with dishka_app(get_with_request, app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

def get_compat(
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_compat(app_provider: AppProvider):
    async with dishka_app(get_compat, app_provider) as client:
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


@inject_sync
def additional(
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
):
    mock(a)


def get_with_depends(
        a: Annotated[None, fastapi.Depends(additional)],
) -> None:
    pass


@pytest.mark.asyncio
async def test_fastapi_depends(app_provider: AppProvider):
    async with dishka_app(get_with_depends, app_provider) as client:
        client.get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
