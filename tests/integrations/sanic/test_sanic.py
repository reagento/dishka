from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from sanic import HTTPResponse, Request, Sanic
from sanic.models.handler_types import RouteHandler

from dishka import make_async_container
from dishka.integrations.sanic import FromDishka, inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


def custom_inject(func: RouteHandler) -> RouteHandler:
    func.__custom__ = True
    return inject(func)


@asynccontextmanager
async def dishka_app(view, provider):
    app = Sanic("test")
    app.get("/")(inject(view))
    container = make_async_container(provider)
    setup_dishka(container, app)
    yield app
    await container.close()


@asynccontextmanager
async def dishka_auto_app(view, provider):
    app = Sanic("test1")
    app.get("/")(view)
    container = make_async_container(provider)
    setup_dishka(container, app, auto_inject=True)
    yield app
    await container.close()


@asynccontextmanager
async def dishka_custom_auto_inject_app(view, provider):
    app = Sanic("test1")
    app.get("/")(view)
    container = make_async_container(provider)
    setup_dishka(container, app, auto_inject=custom_inject)
    yield app
    await container.close()


async def get_with_app(
    _: Request,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)
    return HTTPResponse(status=200)


@pytest.mark.parametrize(
    "app_factory",
    [
        dishka_app,
        dishka_auto_app,
    ],
)
@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider, app_factory):
    async with app_factory(get_with_app, app_provider) as app:
        _, response = await app.asgi_client.get("/")
        assert response.status_code == 200
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


async def get_compat(
    _: Request,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> HTTPResponse:
    mock(a)
    return HTTPResponse(status=200)


@pytest.mark.asyncio
async def test_compat(app_provider: AppProvider):
    async with dishka_app(get_compat, app_provider) as app:
        _, response = await app.asgi_client.get("/")
        assert response.status_code == 200
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


async def handle_for_auto_inject(
    _: Request,
) -> HTTPResponse:
    pass


@pytest.mark.asyncio
async def test_custom_auto_inject(app_provider: AppProvider):
    async with dishka_custom_auto_inject_app(
        handle_for_auto_inject,
        app_provider,
    ) as app:
        _, response = await app.asgi_client.get("/")
        assert getattr(handle_for_auto_inject, "__custom__", False)
