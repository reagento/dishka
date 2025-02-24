from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from taskiq import AsyncBroker, InMemoryBroker

from dishka import FromDishka, Provider, Scope, make_async_container
from dishka.integrations.taskiq import inject, setup_dishka
from .utils import PickleResultBackend

provider = Provider(scope=Scope.REQUEST)
provider.provide(lambda: hash("dishka"), provides=int)


async def return_int_task(data: FromDishka[int]) -> int:
    return data


async def task_with_kwargs(
    _: FromDishka[int],
    **kwargs: str,
) -> dict[str, str]:
    return kwargs


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
@pytest.mark.parametrize(
    "task_func",
    [
        (inject(return_int_task)),
        (inject(patch_module=True)(return_int_task)),
    ],
)
async def test_return_int_task(task_func) -> None:
    async with create_broker() as broker:
        task = broker.task(task_func)
        kiq = await task.kiq()
        result = await kiq.wait_result()
        assert result.return_value == hash("dishka")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "task_func",
    [
        (inject(task_with_kwargs)),
        (inject(patch_module=True)(task_with_kwargs)),
    ],
)
async def test_task_with_kwargs(task_func) -> None:
    async with create_broker() as broker:
        task = broker.task(task_func)
        kwargs = {"key": "value"}

        kiq = await task.kiq(**kwargs)
        result = await kiq.wait_result()

        assert result.return_value == kwargs


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("task_func", "default_name"),
    [
        (inject(return_int_task), "dishka.integrations.base:return_int_task"),
        (
            inject(patch_module=True)(return_int_task),
            "tests.integrations.taskiq.test_taskiq:return_int_task",
        ),
    ],
)
async def test_task_default_name(task_func, default_name) -> None:
    async with create_broker() as broker:
        task = broker.task(task_func)
        assert task.task_name == default_name
