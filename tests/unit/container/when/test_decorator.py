import pytest

from dishka import (
    Marker,
    Provider,
    Scope,
    activator,
    decorate,
    make_container,
    provide,
)


@pytest.mark.parametrize(("active", "value"), [
    (True, "ad"),
    (False, "a"),
])
def test_decorate(*, active: bool, value: str):
    class MyProvider(Provider):
        @activator(Marker("A"))
        def is_active(self):
            return active

        @provide
        def make_str(self) -> str:
            return "a"

        @decorate(when=Marker("A"))
        def decorate_str(self, old_value: str) -> str:
            return old_value + "d"

    c = make_container(MyProvider(scope=Scope.APP))
    assert c.get(str) == value
