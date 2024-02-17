import pytest

from dishka import (
    Provider,
    Scope,
    alias,
    make_async_container,
    make_container,
    provide,
)


def test_cache_sync():
    class MyProvider(Provider):
        value = 0

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
        value = 0

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

def test_nocache_sync():
    class MyProvider(Provider):
        value = 0

        @provide(scope=Scope.REQUEST, cache=False)
        def get_int(self) -> int:
            self.value += 1
            return self.value

    with make_container(MyProvider()) as container:
        with container() as state:
            assert state.get(int) == 1
            assert state.get(int) == 2


@pytest.mark.asyncio
async def test_nocache_async():
    class MyProvider(Provider):
        value = 0

        @provide(scope=Scope.REQUEST, cache=False)
        async def get_int(self) -> int:
            self.value += 1
            return self.value

    async with make_async_container(MyProvider()) as container:
        async with container() as state:
            assert await state.get(int) == 1
            assert await state.get(int) == 2


@pytest.fixture()
def alias_provider():
    class MyProvider(Provider):
        value = 0

        @provide(scope=Scope.APP, cache=False)
        def get_int(self) -> int:
            self.value += 1
            return self.value

        float = alias(source=int, provides=float)
        complex = alias(source=int, provides=complex, cache=False)

    return MyProvider()


def test_alias_sync(alias_provider):
    with make_container(alias_provider) as container:
        assert container.get(int) == 1
        assert container.get(float) == 2
        assert container.get(float) == 2
        assert container.get(complex) == 3
        assert container.get(complex) == 4


@pytest.mark.asyncio
async def test_alias_async(alias_provider):
    async with make_async_container(alias_provider) as container:
        assert await container.get(int) == 1
        assert await container.get(float) == 2
        assert await container.get(float) == 2
        assert await container.get(complex) == 3
        assert await container.get(complex) == 4
