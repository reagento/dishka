import math
from collections.abc import AsyncIterable, Iterable
from unittest.mock import Mock

import pytest

from dishka import (
    DEFAULT_COMPONENT,
    AnyOf,
    DependencyKey,
    Provider,
    Scope,
    alias,
    make_async_container,
    make_container,
    provide,
)
from dishka.exceptions import CycleDependenciesError, NoFactoryError


class AliasProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_int(self) -> int:
        return 42

    aliased_complex = alias(source=float, provides=complex)
    aliased_float = alias(source=int, provides=float)


def test_alias():
    container = make_container(AliasProvider())
    assert container.get(float) == container.get(int)


def test_alias_to_alias():
    container = make_container(AliasProvider())
    assert container.get(complex) == container.get(int)


class CycleProvider(Provider):
    a = alias(source=int, provides=bool)
    b = alias(source=bool, provides=float)
    c = alias(source=float, provides=int)


def test_cycle():
    with pytest.raises(CycleDependenciesError):
        make_container(CycleProvider())


def test_missing_factory():
    p1 = Provider()
    p1.alias(source=bool, provides=float)
    p2 = Provider()
    p2.alias(source=int, provides=bool)
    with pytest.raises(NoFactoryError) as e:
        make_container(p1, p2)
    assert e.value.requested == DependencyKey(int, component=DEFAULT_COMPONENT)


def test_implicit():
    mock = Mock(return_value=42)
    provider = Provider(scope=Scope.APP)
    provider.provide(source=lambda: mock(), provides=AnyOf[float, int])
    container = make_container(provider)
    assert container.get(float) == 42
    assert container.get(int) == 42
    mock.assert_called_once()


def test_implicit_no_source():
    provider = Provider(scope=Scope.APP)
    provider.provide_all(AnyOf[float, str])
    container = make_container(provider)
    assert math.isclose(container.get(float), 0.0, abs_tol=1e-9)
    assert math.isclose(container.get(str), 0.0, abs_tol=1e-9)


def test_implicit_all():
    provider = Provider(scope=Scope.APP)
    provider.provide_all(AnyOf[float, str])
    container = make_container(provider)
    assert math.isclose(container.get(float), 0.0, abs_tol=1e-9)
    assert math.isclose(container.get(str), 0.0, abs_tol=1e-9)


def test_implicit_generator():
    class MyProvider(Provider):
        value = 0

        @provide(scope=Scope.APP)
        def foo(self) -> Iterable[AnyOf[float, int]]:
            self.value += 1
            yield self.value

    container = make_container(MyProvider())
    assert container.get(float) == 1
    assert container.get(int) == 1


def test_implicit_generator_alt():
    class MyProvider(Provider):
        value = 0

        @provide(scope=Scope.APP)
        def foo(self) -> AnyOf[Iterable[float], Iterable[int]]:
            self.value += 1
            yield self.value

    container = make_container(MyProvider())
    assert container.get(float) == 1
    assert container.get(int) == 1


@pytest.mark.asyncio
async def test_implicit_async_generator():
    class MyProvider(Provider):
        value = 0

        @provide(scope=Scope.APP)
        async def foo(self) -> AsyncIterable[AnyOf[float, "int"]]:
            self.value += 1
            yield self.value

    container = make_async_container(MyProvider())
    assert await container.get(float) == 1
    assert await container.get(int) == 1


@pytest.mark.asyncio
async def test_implicit_async_generator_alt():
    class MyProvider(Provider):
        value = 0

        @provide(scope=Scope.APP)
        async def foo(self) -> AnyOf[AsyncIterable[float], AsyncIterable[int]]:
            self.value += 1
            yield self.value

    container = make_async_container(MyProvider())
    assert await container.get(float) == 1
    assert await container.get(int) == 1


def test_union_alias():
    provider = Provider(scope=Scope.APP)
    provider.provide(source=lambda: 42, provides=int)
    provider.alias(source=int, provides=AnyOf[float, complex])
    container = make_container(provider)
    assert container.get(float) == 42
    assert container.get(complex) == 42
