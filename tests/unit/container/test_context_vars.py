import pytest

from dishka import (
    DEFAULT_COMPONENT,
    DependencyKey,
    Provider,
    Scope,
    decorate,
    make_async_container,
    make_container,
    provide,
)
from dishka.dependency_source import from_context
from dishka.exceptions import InvalidGraphError, NoContextValueError


def test_simple():
    provider = Provider()
    provider.from_context(provides=int, scope=Scope.APP)
    provider.from_context(provides=float, scope=Scope.APP)
    container = make_container(provider, context={int: 1})
    container.context[DependencyKey(float, DEFAULT_COMPONENT)] = 2
    assert container.get(int) == 1
    assert container.get(float) == 2
    container.close()
    assert container.get(int) == 1
    assert container.get(float) == 2


@pytest.mark.asyncio
async def test_simple_async():
    provider = Provider()
    provider.from_context(provides=int, scope=Scope.APP)
    provider.from_context(provides=float, scope=Scope.APP)
    container = make_async_container(provider, context={int: 1})
    container.context[DependencyKey(float, DEFAULT_COMPONENT)] = 2
    assert await container.get(int) == 1
    assert await container.get(float) == 2
    await container.close()
    assert await container.get(int) == 1
    assert await container.get(float) == 2


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

        a = from_context(int)

        @provide
        def foo(self, a: int) -> float:
            return a

    container = make_async_container(MyProvider(), context={int: 1})
    assert await container.get(float, component="XXX") == 1


@pytest.mark.asyncio
async def test_2components_factory():
    class MyProvider(Provider):
        scope = Scope.APP
        component = "XXX"

        @provide
        def get_int(self) -> int:
            return 100

        @provide
        def foo(self, a: int) -> float:
            return a

    container = make_async_container(MyProvider(), context={int: 1})
    assert await container.get(float, component="XXX") == 100


def test_decorate():
    class MyProvider(Provider):
        scope = Scope.APP

        i = from_context(int)

        @decorate
        def ii(self, i: int) -> int:
            return i + 1

    with pytest.raises(InvalidGraphError):
        make_container(MyProvider(), context={int: 1})
