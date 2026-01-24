from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Generator,
    Iterable,
    Iterator,
)
from typing import Any

# Deprecated `typing.(Async)Generator` is not the same as
# `collections.abc.(Async)Generator`. Therefore, we need to test support
# for both variants.
from typing import AsyncGenerator as TypingAsyncGenerator  # noqa: UP035
from typing import Generator as TypingGenerator  # noqa: UP035

from dishka import DependencyKey, Scope
from dishka._adaptix.feature_requirement import HAS_TV_DEFAULT
from dishka.dependency_source import Factory
from dishka.dependency_source.composite import CompositeDependencySource
from dishka.entities.factory_type import FactoryType


class ClassA:
    def __init__(self, dep: int) -> None:
        self.dep = dep
        self.closed = False


def sync_func_a(self: Any, dep: int) -> ClassA:
    return ClassA(dep)


def sync_iter_a(self, dep: int) -> Iterable[ClassA]:
    a = ClassA(dep)
    yield a
    a.closed = True


def sync_iterator_a(self, dep: int) -> Iterator[ClassA]:
    a = ClassA(dep)
    yield a
    a.closed = True


def sync_gen_a(self, dep: int) -> Generator[ClassA, None, None]:
    a = ClassA(dep)
    yield a
    a.closed = True


def sync_gen_a_short(self, dep: int) -> Generator[ClassA]:
    a = ClassA(dep)
    yield a
    a.closed = True


def sync_typing_gen_a(self, dep: int) -> TypingGenerator[ClassA, None, None]:
    a = ClassA(dep)
    yield a
    a.closed = True


if HAS_TV_DEFAULT:
    def sync_typing_gen_a_short(self, dep: int) -> TypingGenerator[ClassA]:
        a = ClassA(dep)
        yield a
        a.closed = True


async def async_func_a(self, dep: int) -> ClassA:
    return ClassA(dep)


async def async_iter_a(self, dep: int) -> AsyncIterable[ClassA]:
    a = ClassA(dep)
    yield a
    a.closed = True


async def async_iterator_a(self, dep: int) -> AsyncIterator[ClassA]:
    a = ClassA(dep)
    yield a
    a.closed = True


async def async_gen_a(self, dep: int) -> AsyncGenerator[ClassA, None]:
    a = ClassA(dep)
    yield a
    a.closed = True


async def async_gen_a_short(self, dep: int) -> AsyncGenerator[ClassA]:
    a = ClassA(dep)
    yield a
    a.closed = True


async def async_typing_gen_a(
    self,
    dep: int,
) -> TypingAsyncGenerator[ClassA, None]:
    a = ClassA(dep)
    yield a
    a.closed = True


if HAS_TV_DEFAULT:
    async def async_typing_gen_a_short(
        self,
        dep: int,
    ) -> TypingAsyncGenerator[ClassA]:
        a = ClassA(dep)
        yield a
        a.closed = True


A_VALUE = ClassA(42)
value_factory = Factory(
    provides=DependencyKey(ClassA, None),
    source=A_VALUE,
    dependencies=[],
    kw_dependencies={},
    type_=FactoryType.VALUE,
    scope=Scope.APP,
    is_to_bind=False,
    cache=False,
    when_override=None,
    when_active=None,
    when_component=None,
    when_dependencies={},
)
value_source = CompositeDependencySource(lambda: None, [value_factory])
