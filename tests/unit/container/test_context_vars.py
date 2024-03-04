import pytest

from dishka import (
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from dishka.dependency_source import from_context
from dishka.exceptions import NoContextValueError


def test_simple():
    provider = Provider()
    provider.from_context(provides=int, scope=Scope.APP)
    container = make_container(provider, context={int: 1})
    assert container.get(int) == 1


@pytest.mark.asyncio
async def test_simple_async():
    provider = Provider()
    provider.from_context(provides=int, scope=Scope.APP)
    container = make_async_container(provider, context={int: 1})
    assert await container.get(int) == 1


def test_not_found():
    provider = Provider()
    provider.from_context(provides=int, scope=Scope.APP)
    container = make_container(provider)
    with pytest.raises(NoContextValueError):
        assert container.get(int) == 1


@pytest.mark.asyncio
async def test_not_found_async():
    provider = Provider()
    provider.from_context(provides=int, scope=Scope.APP)
    container = make_async_container(provider)
    with pytest.raises(NoContextValueError):
        assert await container.get(int) == 1


@pytest.mark.asyncio
async def test_2components():
    class MyProvider(Provider):
        scope = Scope.APP
        component = "XXX"

        a = from_context(provides=int)

        @provide
        def foo(self, a: int) -> float:
            return a

    container = make_async_container(MyProvider(), context={int: 1})
    assert await container.get(float, component="XXX") == 1
