from sqlite3 import Connection
from unittest.mock import Mock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.fastapi import setup_dishka


class MockConnectionProvider(Provider):
    @provide(scope=Scope.APP)
    def get_connection(self) -> Connection:
        connection = Mock()
        connection.execute = Mock(return_value="1")
        return connection


@pytest.fixture
def container():
    container = make_async_container(MockConnectionProvider())
    yield container
    container.close()


@pytest.fixture
def client(container):
    app = create_app()
    setup_dishka(container, app)
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def connection(container):
    return await container.get(Connection)
