from typing import Any

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
from ..sample_providers import ClassA


def test_simple():
    provider = Provider()
    provider.from_context(provides=int, scope=Scope.APP)
    container = make_container(provider, context={int: 1})
    assert container.get(int) == 1


class AProvider(Provider):
    scope = Scope.APP
    a = from_context(provides=int)
    b = from_context(provides=str)

    @provide
    def foo(self, a: int) -> ClassA:
        return ClassA(a)

    @provide
    def bar(self, a: str) -> bool:
        return bool(a)


@pytest.mark.parametrize(
    ("context", "expected_count"),
    [
        ({}, 1),
        ({int: 1}, 3),
        ({int: 1, str: "1"}, 5),
    ],
)
def test_simple_resolve_all(context: dict[type, Any], expected_count: int):
    provider = AProvider()
    container = make_container(provider, context=context)
    container.resolve_all()
    assert len(container.context) == expected_count


@pytest.mark.asyncio
async def test_simple_async():
    provider = Provider()
    provider.from_context(provides=int, scope=Scope.APP)
    container = make_async_container(provider, context={int: 1})
    assert await container.get(int) == 1


@pytest.mark.parametrize(
    ("context", "expected_count"),
    [
        ({}, 1),
        ({int: 1}, 3),
        ({int: 1, str: "1"}, 5),
    ],
)
@pytest.mark.asyncio
async def test_simple_resolve_all_async(
    context: dict[type, Any], expected_count: int
):
    provider = AProvider()
    container = make_async_container(provider, context=context)
    await container.resolve_all()
    assert len(container.context) == expected_count


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


@pytest.mark.asyncio
async def test_2components_factory():
    class DefaultProvider(Provider):
        scope = Scope.APP
        a = from_context(provides=int)

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
