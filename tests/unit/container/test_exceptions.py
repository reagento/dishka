from typing import AsyncIterable, Iterable, NewType
from unittest.mock import Mock

import pytest

from dishka import (
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from dishka.exceptions import ExitExceptionGroup


class MyError(Exception):
    pass


SyncError = NewType("SyncError", int)
SyncFinalizationError = NewType("SyncFinalizationError", int)
AsyncError = NewType("SyncError", int)
AsyncFinalizationError = NewType("SyncFinalizationError", int)


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
    with pytest.raises(ExitExceptionGroup):
        container = make_container(MyProvider(finalizer))
        container.get(dep_type)
        container.close()
    finalizer.assert_called_once()


@pytest.mark.parametrize("dep_type", [
    SyncFinalizationError,
    AsyncFinalizationError,
])
@pytest.mark.asyncio
async def test_async(dep_type):
    finalizer = Mock(return_value=123)
    with pytest.raises(ExitExceptionGroup):
        container = make_async_container(MyProvider(finalizer))
        await container.get(dep_type)
        await container.close()
    finalizer.assert_called_once()
