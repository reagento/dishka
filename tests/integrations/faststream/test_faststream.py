from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import Mock

import pytest
from faststream import FastStream
from faststream.nats import NatsBroker, TestNatsBroker

from dishka import make_async_container
from dishka.integrations.faststream import (
    FromDishka,
    inject,
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
async def dishka_app(
    view: Callable[..., Any],
    provider: AppProvider,
) -> AsyncIterator[NatsBroker]:
    broker = NatsBroker()
    broker.subscriber("test")(inject(view))

    app = FastStream(broker)

    container = make_async_container(provider)
    setup_dishka(container, app=app)

    async with TestNatsBroker(broker) as br:
        yield br

    await container.close()


async def get_with_app(
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider) -> None:
    async with dishka_app(get_with_app, app_provider) as client:
        assert await client.publish("", "test", rpc=True) == "passed"

        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


async def get_with_request(
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> str:
    mock(a)
    return "passed"


@pytest.mark.asyncio
async def test_request_dependency(app_provider: AppProvider) -> None:
    async with dishka_app(get_with_request, app_provider) as client:
        assert await client.publish("", "test", rpc=True) == "passed"

        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_autoinject_before_subscriber(app_provider: AppProvider) -> None:
    broker = NatsBroker()
    app = FastStream(broker)

    container = make_async_container(app_provider)
    setup_dishka(container, app=app, auto_inject=True)

    broker.subscriber("test")(get_with_request)

    async with TestNatsBroker(broker) as br:
        assert await br.publish("", "test", rpc=True) == "passed"

        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

    await container.close()


@pytest.mark.asyncio
async def test_autoinject_after_subscriber(app_provider: AppProvider) -> None:
    broker = NatsBroker()
    app = FastStream(broker)

    broker.subscriber("test")(get_with_request)

    container = make_async_container(app_provider)
    setup_dishka(container, app=app, auto_inject=True)

    async with TestNatsBroker(broker) as br:
        assert await br.publish("", "test", rpc=True) == "passed"

        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

    await container.close()


@pytest.mark.asyncio
async def test_faststream_with_broker(app_provider: AppProvider) -> None:
    broker = NatsBroker()
    broker.subscriber("test")(get_with_request)
    container = make_async_container(app_provider)
    setup_dishka(container, broker=broker, auto_inject=True)

    async with TestNatsBroker(broker) as br:
        assert await br.publish("", "test", rpc=True) == "passed"

        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

    await container.close()
