from typing import AsyncGenerator, AsyncIterable, Generator, Iterable

from dishka import Scope
from dishka.dependency_source import Factory, FactoryType


class ClassA:
    def __init__(self, dep: int) -> None:
        self.dep = dep
        self.closed = False


def sync_func_a(self, dep: int) -> ClassA:
    return ClassA(dep)


def sync_iter_a(self, dep: int) -> Iterable[ClassA]:
    a = ClassA(dep)
    yield a
    a.closed = True


def sync_gen_a(self, dep: int) -> Generator[None, ClassA, None]:
    a = ClassA(dep)
    yield a
    a.closed = True


async def async_func_a(self, dep: int) -> ClassA:
    return ClassA(dep)


async def async_iter_a(self, dep: int) -> AsyncIterable[ClassA]:
    a = ClassA(dep)
    yield a
    a.closed = True


async def async_gen_a(self, dep: int) -> AsyncGenerator[ClassA, None]:
    a = ClassA(dep)
    yield a
    a.closed = True


A_VALUE = ClassA(42)
value_factory = Factory(
    provides=ClassA,
    source=A_VALUE,
    dependencies=[],
    type=FactoryType.VALUE,
    scope=Scope.APP,
    is_to_bound=False,
    cache=False,
)
