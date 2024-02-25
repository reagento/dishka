from typing import Annotated

import pytest

from dishka import Provider, Scope, make_container, provide
from dishka.dependency_source.key import FromComponent
from dishka.exceptions import NoFactoryError


def test_from_component():
    class MainProvider(Provider):
        scope = Scope.APP

        @provide
        def foo(self, a: Annotated[int, FromComponent("X")]) -> float:
            return a * 10

    class XProvider(Provider):
        scope = Scope.APP
        component = "X"

        @provide
        def foo(self) -> int:
            return 42

    container = make_container(MainProvider(), XProvider())
    assert container.get(float) == 420
    assert container.get(int, component="X") == 42
    with pytest.raises(NoFactoryError):
        container.get(int)
