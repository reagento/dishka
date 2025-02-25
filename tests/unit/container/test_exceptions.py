from collections.abc import AsyncIterable, Iterable
from typing import Annotated, NewType
from unittest.mock import Mock

import pytest

from dishka import (
    DEFAULT_COMPONENT,
    DependencyKey,
    FromComponent,
    Provider,
    Scope,
    from_context,
    make_async_container,
    make_container,
    provide,
)
from dishka.exception_base import (
    ExitError, NoContextValueError, UnsupportedFactoryError
)
from dishka.exceptions import NoFactoryError
from dishka.exceptions import UnknownScopeError


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


def test_no_factory_cls_sync():
    class A:
        def __init__(self, *, x: object):
            pass
    provider = Provider(scope=Scope.APP)
    provider.provide(A)
    with pytest.raises(NoFactoryError) as e:
        make_container(provider)
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


def test_invalid_type_sync():
    class A:
        def __init__(self, x: "B"):  # noqa: F821
            pass
    provider = Provider(scope=Scope.APP)
    with pytest.raises(NameError):
        provider.provide(A)


def test_no_type_sync():
    class A:
        def __init__(self, x):
            pass
    provider = Provider(scope=Scope.APP)
    with pytest.raises(ValueError):  # noqa: PT011
        provider.provide(A)


class MissingFactoryProvider(Provider):
    @provide(scope=Scope.APP)
    def x(self, value: object) -> int:
        return 1

    @provide(scope=Scope.APP)
    def a(self, value: int) -> float:
        return value

    @provide(scope=Scope.APP)
    def b(self, *, value: float) -> complex:
        return value


def test_no_factory_init_sync():
    with pytest.raises(NoFactoryError) as e:
        make_container(MissingFactoryProvider())
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


@pytest.mark.asyncio
async def test_no_factory_init_async():
    with pytest.raises(NoFactoryError) as e:
        make_async_container(MissingFactoryProvider())
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


def test_no_factory_sync():
    container = make_container(Provider())
    with pytest.raises(NoFactoryError) as e:
        container.get(object)
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)
    assert str(e.value)


def test_no_factory_path_sync():
    container = make_container(MissingFactoryProvider(), skip_validation=True)
    with pytest.raises(NoFactoryError) as e:
        container.get(complex)
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)
    assert str(e.value)


@pytest.mark.asyncio
async def test_no_factory_async():
    container = make_async_container(Provider())
    with pytest.raises(NoFactoryError) as e:
        await container.get(object)
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


@pytest.mark.asyncio
async def test_no_factory_path_async():
    container = make_async_container(
        MissingFactoryProvider(), skip_validation=True,
    )
    with pytest.raises(NoFactoryError) as e:
        await container.get(complex)
    assert e.value.requested == DependencyKey(object, DEFAULT_COMPONENT)


class AsyncProvider(Provider):
    @provide(scope=Scope.APP)
    async def x(self) -> int:
        return 0


def test_async_factory_in_sync():
    container = make_container(AsyncProvider())
    with pytest.raises(UnsupportedFactoryError):
        container.get(int)


def test_invalid_scope_factory():
    class InvalidScopeProvider(Provider):
        @provide(scope="invalid")
        def foo(self) -> int:
            return 1

    with pytest.raises(UnknownScopeError):
        make_container(InvalidScopeProvider())


def test_missing_context_var_sync():
    class MyProvider(Provider):
        a = from_context(int, scope=Scope.APP)

    container = make_container(MyProvider())
    with pytest.raises(NoContextValueError):
        container.get(int)


@pytest.mark.asyncio
async def test_missing_context_var_async():
    class MyProvider(Provider):
        a = from_context(int, scope=Scope.APP)

    container = make_async_container(MyProvider())
    with pytest.raises(NoContextValueError):
        await container.get(int)


def test_no_scope():
    class NoScopeProvider(Provider):
        @provide
        def x(self) -> int:
            return 1

    with pytest.raises(ValueError):  # noqa: PT011
        NoScopeProvider()


class InvalidScopeProvider(Provider):
    @provide(scope=Scope.APP)
    def get_int(self, value: object) -> int:
        return value

    @provide(scope=Scope.REQUEST)
    def get_obj(self) -> object:
        return 1

    @provide(scope=Scope.APP)
    def get_obj_x(self) -> Annotated[object, FromComponent("x")]:
        return 2

def test_invalid_scope():
    with pytest.raises(NoFactoryError) as e:
        make_container(InvalidScopeProvider())

    assert str(e.value)
    assert len(e.value.suggest_other_scopes) == 1
    assert e.value.suggest_other_scopes[0].scope == Scope.REQUEST
    assert e.value.suggest_other_scopes[0].provides == DependencyKey(
        object, DEFAULT_COMPONENT,
    )
    assert len(e.value.suggest_other_components) == 1
    assert e.value.suggest_other_components[0].scope == Scope.APP
    assert e.value.suggest_other_components[0].provides == DependencyKey(
        object, "x",
    )
