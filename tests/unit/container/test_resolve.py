import pytest

from dishka import (
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from ..sample_providers import (
    A_VALUE,
    ClassA,
    async_func_a,
    async_gen_a,
    async_iter_a,
    sync_func_a,
    sync_gen_a,
    sync_iter_a,
    value_factory,
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


def test_value():
    class MyProvider(Provider):
        factory = value_factory

    with make_container(MyProvider()) as container:
        assert container.get(ClassA) is A_VALUE


@pytest.mark.asyncio
async def test_value_async():
    class MyProvider(Provider):
        factory = value_factory

    async with make_async_container(MyProvider()) as container:
        assert await container.get(ClassA) is A_VALUE
