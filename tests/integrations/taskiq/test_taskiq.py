from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from taskiq import AsyncBroker, InMemoryBroker

from dishka import FromDishka, Provider, Scope, make_async_container
from dishka.integrations.taskiq import inject, setup_dishka
from .utils import PickleResultBackend

provider = Provider(scope=Scope.REQUEST)
provider.provide(lambda: hash("dishka"), provides=int)


@inject
async def return_int_task(data: FromDishka[int]) -> int:
    return data


@asynccontextmanager
async def create_broker() -> AsyncIterator[AsyncBroker]:
    in_memory_broker = InMemoryBroker().with_result_backend(
        PickleResultBackend(),
    )
    container = make_async_container(provider)
    setup_dishka(
        container,
        in_memory_broker,
    )

    await in_memory_broker.startup()
    yield in_memory_broker
    await in_memory_broker.shutdown()
    await container.close()


@pytest.mark.asyncio
async def test_return_int_task() -> None:
    async with create_broker() as broker:
        task = broker.task(return_int_task)
        kiq = await task.kiq()
        result = await kiq.wait_result()
        assert result.return_value == hash("dishka")
