from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from inspect import isfunction
from unittest.mock import Mock

import pytest
from blacksheep import Application as Blacksheep
from blacksheep import Response
from blacksheep.server.controllers import APIController
from blacksheep.server.controllers import get as controller_get
from blacksheep.testing import TestClient

from dishka import make_async_container
from dishka.integrations.blacksheep import setup_dishka
from ..common import APP_DEP_VALUE, AppDep, AppProvider


@asynccontextmanager
async def dishka_app(
    view_or_controller,
    provider,
) -> AsyncGenerator[TestClient, None]:
    app = Blacksheep()

    container = make_async_container(provider)
    setup_dishka(container, app)

    if isfunction(view_or_controller):
        app.router.add_get("/", view_or_controller)
    else:
        assert issubclass(view_or_controller, APIController)

    await app.start()
    yield TestClient(app)
    await app.stop()

    await container.close()


async def get_with_app(a: AppDep, mock: Mock) -> None:
    mock(a)


class TestController(APIController):
    def __init__(self, a: AppDep, mock: Mock) -> None:
        self.a = a
        self.mock = mock

    @classmethod
    def route(cls) -> str:
        return "controller"

    @controller_get("/")
    async def index(self) -> Response:
        self.mock(self.a)
        return self.ok()


@pytest.mark.parametrize("app_factory", [dishka_app])
@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider, app_factory):
    async with app_factory(get_with_app, app_provider) as client:
        await client.get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


@pytest.mark.parametrize("app_factory", [dishka_app])
@pytest.mark.asyncio
async def test_app_controller_dependency(
    app_provider: AppProvider,
    app_factory,
):
    async with app_factory(TestController, app_provider) as client:
        await client.get("/controller")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()
