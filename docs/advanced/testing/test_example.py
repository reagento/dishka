from collections.abc import Iterable
from sqlite3 import Connection, connect
from typing import Annotated
from unittest.mock import Mock

import pytest
import pytest_asyncio
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import FromDishka, inject, setup_dishka

router = APIRouter()


@router.get("/")
@inject
async def index(connection: FromDishka[Connection]) -> str:
    connection.execute("select 1")
    return "Ok"


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


class ConnectionProvider(Provider):
    def __init__(self, uri):
        super().__init__()
        self.uri = uri

    @provide(scope=Scope.REQUEST)
    def get_connection(self) -> Iterable[Connection]:
        conn = connect(self.uri)
        yield conn
        conn.close()


def create_production_app():
    app = create_app()
    container = make_async_container(ConnectionProvider("sqlite:///"))
    setup_dishka(container, app)
    return app


class MockConnectionProvider(Provider):
    @provide(scope=Scope.APP)
    def get_connection(self) -> Connection:
        connection = Mock()
        connection.execute = Mock(return_value="1")
        return connection


@pytest_asyncio.fixture
async def container():
    container = make_async_container(MockConnectionProvider())
    yield container
    await container.close()


@pytest.fixture
def client(container):
    app = create_app()
    setup_dishka(container, app)
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def connection(container):
    return await container.get(Connection)


@pytest.mark.asyncio
async def test_controller(client: TestClient, connection: Mock):
    response = client.get("/")
    assert response.status_code == 200
    connection.execute.assert_called()
