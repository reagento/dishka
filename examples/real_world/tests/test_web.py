"""
In this test example we mock our interactors to check if web view
works correctly. Other option was to only adapters or just use real providers.

We use `fastapi.testclient.TestClient` to send requests to the app
Additionally we need `asgi_lifespan.LifespanManager` to correctly enter
app scope as it is done in real application
"""
from unittest.mock import Mock

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi.testclient import TestClient

from dishka import Provider, Scope, provide
from dishka.integrations.fastapi import (
    DishkaApp,
)
from main_web import create_fastapi_app
from myapp.use_cases import AddProductsInteractor


class FakeInteractorProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def add_products(self) -> AddProductsInteractor:
        return Mock()


@pytest.fixture
def interactor_provider():
    return FakeInteractorProvider()


@pytest_asyncio.fixture
async def client(interactor_provider):
    app = DishkaApp(
        providers=[interactor_provider],
        app=create_fastapi_app(),
    )
    async with LifespanManager(app):
        yield TestClient(app)


@pytest.mark.asyncio
async def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == "Ok"
