import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock

import pytest

from dishka import (
    AsyncContainer,
    Container,
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)


class SyncProvider(Provider):
    def __init__(self, event: threading.Event, mock: Mock):
        super().__init__()
        self.event = event
        self.mock = mock

    @provide(scope=Scope.APP)
    def get_int(self) -> int:
        self.event.wait()
        return self.mock()

    @provide(scope=Scope.APP)
    def get_str(self, value: int) -> str:
        return "str"


def sync_get(container: Container):
    container.get(str)


@pytest.mark.repeat(10)
def test_cache_sync():
    int_getter = Mock(return_value=123)
    event = threading.Event()
    provider = SyncProvider(event, int_getter)
    with ThreadPoolExecutor() as pool:
        with make_container(provider, with_lock=True) as container:
            pool.submit(sync_get, container)
            pool.submit(sync_get, container)
            time.sleep(0.01)
            event.set()
    int_getter.assert_called_once_with()


class AsyncProvider(Provider):
    def __init__(self, event: asyncio.Event, mock: Mock):
        super().__init__()
        self.event = event
        self.mock = mock

    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await self.event.wait()
        return self.mock()

    @provide(scope=Scope.APP)
    def get_str(self, value: int) -> str:
        return "str"


async def async_get(container: AsyncContainer):
    await container.get(str)


@pytest.mark.repeat(10)
@pytest.mark.asyncio
async def test_cache_async():
    int_getter = Mock(return_value=123)
    event = asyncio.Event()
    provider = AsyncProvider(event, int_getter)

    async with make_async_container(provider, with_lock=True) as container:
        t1 = asyncio.create_task(async_get(container))
        t2 = asyncio.create_task(async_get(container))
        await asyncio.sleep(0.01)
        event.set()
        await t1
        await t2

    int_getter.assert_called_once_with()
