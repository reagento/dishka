from collections.abc import AsyncIterable, Iterable
from typing import NewType
from unittest.mock import Mock

import pytest

from dishka import (
    DEFAULT_COMPONENT,
    DependencyKey,
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from dishka.exceptions import (
    ExitError,
    NoFactoryError,
    UnsupportedFactoryError,
)


class MyError(Exception):
    pass


SyncError = NewType("SyncError", int)
SyncFinalizationError = NewType("SyncFinalizationError", int)
AsyncError = NewType("AsyncError", int)
AsyncFinalizationError = NewType("AsyncFinalizationError", int)


class MyProvider(Provider):
    def __init__(self, release_mock: Mock):
        super().__init__()
        self.release_mock = release_mock

    @provide(scope=Scope.APP)
    def get_int(self) -> Iterable[int]:
        yield 1
        self.release_mock()

    @provide(scope=Scope.APP)
    def get1(self, value: int) -> SyncError:
        raise MyError

    @provide(scope=Scope.APP)
    def get2(self, value: int) -> Iterable[SyncFinalizationError]:
        yield value
        raise MyError

    @provide(scope=Scope.APP)
    async def get3(self, value: int) -> AsyncError:
        raise MyError

    @provide(scope=Scope.APP)
    async def get4(self, value: int) -> AsyncIterable[AsyncFinalizationError]:
        yield value
        raise MyError


@pytest.mark.parametrize("dep_type", [
    SyncFinalizationError,
])
def test_sync(dep_type):
    finalizer = Mock(return_value=123)
    container = make_container(MyProvider(finalizer))
    container.get(dep_type)
    with pytest.raises(ExitError):
        container.close()
    finalizer.assert_called_once()


@pytest.mark.parametrize("dep_type", [
    SyncFinalizationError,
    AsyncFinalizationError,
])
@pytest.mark.asyncio
async def test_async(dep_type):
    finalizer = Mock(return_value=123)
    container = make_async_container(MyProvider(finalizer))
    await container.get(dep_type)
    with pytest.raises(ExitError):
        await container.close()
    finalizer.assert_called_once()


class InvalidScopeProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def y(self) -> object:
        return False

    @provide(scope=Scope.APP)
    def x(self, value: object) -> int:
        return 1

    @provide(scope=Scope.APP)
    def a(self, value: int) -> float:
        return value

    @provide(scope=Scope.APP)
    def b(self, value: float) -> complex:
        return value


def test_no_factory_init_sync():
    with pytest.raises(NoFactoryError) as e:
        make_container(InvalidScopeProvider())
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


@pytest.mark.asyncio
async def test_no_factory_init_async():
    with pytest.raises(NoFactoryError) as e:
        make_async_container(InvalidScopeProvider())
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


def test_no_factory_sync():
    container = make_container(Provider())
    with pytest.raises(NoFactoryError) as e:
        container.get(object)
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


@pytest.mark.asyncio
async def test_no_factory_async():
    container = make_async_container(Provider())
    with pytest.raises(NoFactoryError) as e:
        await container.get(object)
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


class AsyncProvider(Provider):
    @provide(scope=Scope.APP)
    async def x(self) -> int:
        return 0


def test_async_factory_in_sync():
    container = make_container(AsyncProvider())
    with pytest.raises(UnsupportedFactoryError):
        container.get(int)
