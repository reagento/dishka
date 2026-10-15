from enum import Enum, auto
from typing import Protocol

import pytest

from dishka import (
    Provider,
    Scope,
    alias,
    decorate,
    make_async_container,
    make_container,
    provide,
)
from dishka.plotter import render_d2, render_mermaid


class P(Protocol):
    pass


class MyProvider(Provider):
    component = "XXX"

    @provide(scope=Scope.APP)
    def foo(self) -> int:
        return 1

    @provide(scope=Scope.REQUEST)
    def bar(self, i: int) -> P:
        ...

    @decorate
    def foobar(self, i: int) -> int:
        return i

    float_alias = alias(source=int, provides=float)


class Comp(Enum):
    DB = auto()


ANON = object()


class EnumComponentProvider(Provider):
    component = Comp.DB

    @provide(scope=Scope.APP)
    def value(self) -> int:
        return 1


class ObjectComponentProvider(Provider):
    component = ANON

    @provide(scope=Scope.APP)
    def value(self) -> float:
        return 1.0


@pytest.mark.parametrize("container", [
    make_container(MyProvider()),
    make_async_container(MyProvider()),
    make_container(EnumComponentProvider(), ObjectComponentProvider()),
    make_async_container(EnumComponentProvider(), ObjectComponentProvider()),
])
@pytest.mark.parametrize("renderer", [
    render_d2, render_mermaid,
])
def test_wrapper(container, renderer):
    assert renderer(container)
