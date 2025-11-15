from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import Mock

import pytest
import strawberry
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from fastapi.testclient import TestClient
from strawberry.fastapi import GraphQLRouter

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from dishka.integrations.strawberry import FromDishka, inject
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    Provider,
    RequestDep,
)


@asynccontextmanager
async def create_strawberry_app(
    query_type: type, provider: Provider,
) -> AsyncIterator[TestClient]:
    schema = strawberry.Schema(query=query_type)
    graphql_router = GraphQLRouter(schema)

    app = FastAPI()
    app.include_router(graphql_router, prefix="/graphql")

    container = make_async_container(provider)
    setup_dishka(container, app)

    async with LifespanManager(app):
        yield TestClient(app)
    await container.close()


@strawberry.type
class AppDepQuery:
    @strawberry.field
    @inject
    async def get_app(
        self,
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
    ) -> str:
        mock(a)
        return a


@strawberry.type
class RequestDepQuery:
    @strawberry.field
    @inject
    async def get_request(
        self,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
    ) -> str:
        mock(a)
        return a


@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider):
    async with create_strawberry_app(AppDepQuery, app_provider) as client:
        response = client.post(
            "/graphql",
            json={"query": "{ getApp }"},
        )
        assert response.status_code == 200
        assert response.json() == {"data": {"getApp": APP_DEP_VALUE}}
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


@pytest.mark.asyncio
async def test_request_dependency(app_provider: AppProvider):
    async with create_strawberry_app(RequestDepQuery, app_provider) as client:
        response = client.post(
            "/graphql",
            json={"query": "{ getRequest }"},
        )
        assert response.status_code == 200
        expected = {"data": {"getRequest": REQUEST_DEP_VALUE}}
        assert response.json() == expected
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
