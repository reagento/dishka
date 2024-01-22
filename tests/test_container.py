import pytest

from dishka import (
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from .sample_providers import (
    ClassA,
    async_func_a,
    async_gen_a,
    async_iter_a,
    sync_func_a,
    sync_gen_a,
    sync_iter_a,
)


@pytest.mark.parametrize(
    "factory, closed", [
        (ClassA, False),
        (sync_func_a, False),
        (sync_iter_a, True),
        (sync_gen_a, True),
    ],
)
def test_sync(factory, closed):
    class MyProvider(Provider):
        a = provide(factory, scope=Scope.APP)

        @provide(scope=Scope.APP)
        def get_int(self) -> int:
            return 100

    with make_container(MyProvider()) as container:
        a = container.get(ClassA)
        assert a
        assert a.dep == 100
    assert a.closed == closed


@pytest.mark.parametrize(
    "factory, closed", [
        (ClassA, False),
        (sync_func_a, False),
        (sync_iter_a, True),
        (sync_gen_a, True),
        (async_func_a, False),
        (async_iter_a, True),
        (async_gen_a, True),
    ],
)
@pytest.mark.asyncio
async def test_async(factory, closed):
    class MyProvider(Provider):
        a = provide(factory, scope=Scope.APP)

        @provide(scope=Scope.APP)
        def get_int(self) -> int:
            return 100

    async with make_async_container(MyProvider()) as container:
        a = await container.get(ClassA)
        assert a
        assert a.dep == 100
    assert a.closed == closed


def test_cache_sync():
    class MyProvider(Provider):
        def __init__(self):
            super().__init__()
            self.value = 0

        @provide(scope=Scope.REQUEST)
        def get_int(self) -> int:
            self.value += 1
            return self.value

    with make_container(MyProvider()) as container:
        with container() as state:
            assert state.get(int) == 1
            assert state.get(int) == 1
        with container() as state:
            assert state.get(int) == 2
            assert state.get(int) == 2


@pytest.mark.asyncio
async def test_cache_async():
    class MyProvider(Provider):
        def __init__(self):
            super().__init__()
            self.value = 0

        @provide(scope=Scope.REQUEST)
        async def get_int(self) -> int:
            self.value += 1
            return self.value

    async with make_async_container(MyProvider()) as container:
        async with container() as state:
            assert await state.get(int) == 1
            assert await state.get(int) == 1
        async with container() as state:
            assert await state.get(int) == 2
            assert await state.get(int) == 2
