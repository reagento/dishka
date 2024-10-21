import pytest

from dishka import (
    Provider,
    Scope,
    alias,
    make_async_container,
    make_container,
    provide,
)
from dishka.plotter import render_d2, render_mermaid


class MyProvider(Provider):
    component = "XXX"
    @provide(scope=Scope.APP)
    def foo(self) -> int:
        return 1

    float_alias = alias(source=int, provides=float)


@pytest.mark.parametrize("container", [
    make_container(MyProvider()),
    make_async_container(MyProvider()),
])
@pytest.mark.parametrize("renderer", [
    render_d2, render_mermaid,
])
def test_wrapper(container, renderer):
    assert renderer(container)
