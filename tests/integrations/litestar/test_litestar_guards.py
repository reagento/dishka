from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from litestar import Litestar, get
from litestar.connection import ASGIConnection
from litestar.handlers import BaseRouteHandler
from litestar.guards import Guard
from litestar.testing import TestClient

from dishka import make_async_container
from dishka.integrations.litestar import (
    DishkaRouter,
    FromDishka,
    inject_asgi,
    setup_dishka,
)
from ..common import (
    APP_DEP_VALUE,
    AppDep,
    AppProvider,
)


@asynccontextmanager
async def dishka_app(guard: Guard, provider: AppProvider) -> AsyncGenerator[TestClient, None]:
    @get("/", guards=[guard])
    async def endpoint() -> dict:
        return {"status": "ok"}

    app = Litestar([endpoint], debug=True)
    container = make_async_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield TestClient(app)
    await container.close()


@asynccontextmanager
async def dishka_auto_app(guard: Guard, provider: AppProvider) -> AsyncGenerator[TestClient, None]:
    @get("/")
    async def endpoint() -> dict:
        return {"status": "ok"}

    router = DishkaRouter("", route_handlers=[endpoint], guards=[guard])
    app = Litestar([router], debug=True)
    container = make_async_container(provider)
    setup_dishka(container, app)
    async with LifespanManager(app):
        yield TestClient(app)
    await container.close()


@inject_asgi
async def guard_with_app(
    connection: ASGIConnection,
    _: BaseRouteHandler,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


async def auto_guard_with_app(
    connection: ASGIConnection,
    _: BaseRouteHandler,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("app_factory", "guard"),
    [
        (dishka_app, guard_with_app),
        (dishka_auto_app, auto_guard_with_app),
    ],
)
async def test_guard_injects_app_dependency(
    app_factory,
    guard,
    app_provider: AppProvider,
):
    async with app_factory(guard, app_provider) as client:
        response = client.get("/")
        assert response.status_code == 200
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
