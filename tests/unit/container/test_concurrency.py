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
        container = make_container(provider, lock_factory=threading.Lock)
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

    container = make_async_container(provider, lock_factory=asyncio.Lock)
    t1 = asyncio.create_task(async_get(container))
    t2 = asyncio.create_task(async_get(container))
    await asyncio.sleep(0.01)
    event.set()
    await t1
    await t2

    int_getter.assert_called_once_with()


# --- Approach B: Pending dedup & gather tests ---


class PendingDedupProvider(Provider):
    """Provider where the int factory is slow — used to test dedup."""

    def __init__(self, mock: Mock):
        super().__init__()
        self.mock = mock

    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.05)
        return self.mock()

    @provide(scope=Scope.APP)
    def get_str(self, value: int) -> str:
        return str(value)


@pytest.mark.repeat(10)
@pytest.mark.asyncio
async def test_pending_dedup_no_lock():
    """Concurrent gets without lock — pending dedup works."""
    int_getter = Mock(return_value=42)
    provider = PendingDedupProvider(int_getter)

    container = make_async_container(provider, lock_factory=None)
    t1 = asyncio.create_task(container.get(str))
    t2 = asyncio.create_task(container.get(str))
    r1, r2 = await asyncio.gather(t1, t2)

    int_getter.assert_called_once_with()
    assert r1 == "42"
    assert r2 == "42"
    await container.close()


class FailingProvider(Provider):
    def __init__(self, mock: Mock):
        super().__init__()
        self.mock = mock

    @provide(scope=Scope.APP)
    async def get_int(self) -> int:
        await asyncio.sleep(0.05)
        return self.mock()


@pytest.mark.asyncio
async def test_pending_exception_propagation():
    """If a pending dep fails, waiters get the exception; retry works."""
    call_count = 0

    def failing_then_ok():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("boom")
        return 42

    mock = Mock(side_effect=failing_then_ok)
    provider = FailingProvider(mock)
    container = make_async_container(provider, lock_factory=None)

    # First concurrent calls — both should fail
    t1 = asyncio.create_task(container.get(int))
    t2 = asyncio.create_task(container.get(int))

    results = await asyncio.gather(t1, t2, return_exceptions=True)
    assert all(isinstance(r, ValueError) for r in results)
    assert mock.call_count == 1  # only one actual call

    # Retry should work (pending removed from cache)
    result = await container.get(int)
    assert result == 42
    await container.close()
