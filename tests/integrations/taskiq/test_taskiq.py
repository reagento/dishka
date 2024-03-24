from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from taskiq import AsyncBroker, InMemoryBroker

from dishka import FromDishka, Provider, Scope, make_async_container
from dishka.integrations.taskiq import inject, setup_dishka

provider = Provider(scope=Scope.REQUEST)
provider.provide(lambda: hash("adaptix"), provides=int)

@inject
async def task_handler(other_hash: FromDishka[int]) -> int:
    return other_hash


@asynccontextmanager
async def create_broker() -> AsyncIterator[AsyncBroker]:
    broker = InMemoryBroker()
    container = make_async_container(provider)
    setup_dishka(
        container,
        broker,
    )

    await broker.startup()
    yield broker
    await broker.shutdown()
    await container.close()


@pytest.mark.asyncio
async def test_depends() -> None:
    async with create_broker() as broker:
        task = broker.task(task_handler)
        kiq = await task.kiq()
        result = await kiq.wait_result()
    assert result.return_value == hash("adaptix")
