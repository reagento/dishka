from typing import Annotated

import pytest

from dishka import (
    FromComponent,
    Provider,
    Scope,
    alias,
    make_container,
    provide,
)
from dishka.exceptions import NoFactoryError


class MainProvider(Provider):
    scope = Scope.APP

    @provide
    def foo(self, a: Annotated[float, FromComponent("X")]) -> complex:
        return a * 10

    @provide
    def bar(self) -> int:
        return 20


class AliasedProvider(Provider):
    scope = Scope.APP

    float_alias = alias(source=float, component="X")

    @provide
    def foo(self, a: float) -> complex:
        return a * 10

    @provide
    def bar(self) -> int:
        return 20


class XProvider(Provider):
    scope = Scope.APP
    component = "X"

    @provide
    def foo(self, a: Annotated[int, FromComponent()]) -> float:
        return a + 1


def test_from_component():
    container = make_container(MainProvider(), XProvider())
    assert container.get(complex) == 210
    assert container.get(float, component="X") == 21
    with pytest.raises(NoFactoryError):
        container.get(float)


def test_from_component_alias():
    container = make_container(AliasedProvider(), XProvider())
    assert container.get(complex) == 210
    assert container.get(float, component="X") == 21
    assert container.get(float) == 21
