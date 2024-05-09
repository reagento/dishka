from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
from blacksheep import Application as Blacksheep
from blacksheep import Response
from blacksheep.server.controllers import APIController
from blacksheep.server.controllers import get as controller_get
from blacksheep.testing import TestClient

from dishka import make_async_container
from dishka.integrations.blacksheep import setup_dishka
from ..common import AppDep, AppProvider


@asynccontextmanager
async def dishka_app(view, provider) -> AsyncGenerator[TestClient, None]:
    app = Blacksheep()

    container = make_async_container(provider)
    setup_dishka(container, app)

    if not issubclass(view, APIController):
        app.router.add_get("/", view)

    await app.start()
    yield TestClient(app)
    await app.stop()


async def get_with_app(a: AppDep, mock: Mock) -> None:
    mock(a)


class TestController(APIController):
    mock: Mock

    @classmethod
    def route(cls) -> str:
        return "controller"

    @controller_get("/")
    async def index(self) -> Response:
        return self.ok("hi")


@pytest.mark.parametrize("app_factory", [dishka_app])
@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider, app_factory):
    async with app_factory(get_with_app, app_provider) as client:
        await client.get("/")


@pytest.mark.parametrize("app_factory", [dishka_app])
@pytest.mark.asyncio
async def test_app_controller_dependency(
    app_provider: AppProvider,
    app_factory,
):
    async with app_factory(TestController, app_provider) as client:
        resp = await client.get("/controller")
        assert resp.status == 200
