import pytest

from dishka import (
    STRICT_VALIDATION,
    Has,
    Marker,
    Provider,
    Scope,
    activate,
    decorate,
    make_container,
    provide,
)
from dishka.exceptions import ImplicitOverrideDetectedError


@pytest.mark.parametrize(("active", "value"), [
    (True, "ad"),
    (False, "a"),
])
def test_decorate(*, active: bool, value: str):
    class MyProvider(Provider):
        @activate(Marker("A"))
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


@pytest.mark.parametrize(("active", "value"), [
    (True, "ad"),
    (False, "a"),
])
def test_decorate_selector(*, active: bool, value: str):
    class MyProvider(Provider):
        @activate(Marker("A"))
        def is_active(self):
            return active

        @provide
        def make_str(self) -> str:
            return "a"

        @provide(when=Has(float))
        def make_str2(self) -> str:
            return "b"

        @decorate(when=Marker("A"))
        def decorate_str(self, old_value: str) -> str:
            return old_value + "d"

    c = make_container(MyProvider(scope=Scope.APP))
    assert c.get(str) == value


def test_decorate_override():
    class MyProvider(Provider):
        @provide
        def make_str(self) -> str:
            return "a"

        @provide(override=True)
        def make_str2(self) -> str:
            return "b"

        @decorate(when=Has(float))
        def decorate_str(self, old_value: str) -> str:
            return old_value + "d"

    c = make_container(
        MyProvider(scope=Scope.APP),
        validation_settings=STRICT_VALIDATION,
    )
    assert c.get(str) == "b"


def test_decorate_override_implicit():
    class MyProvider(Provider):
        @provide
        def make_str(self) -> str:
            return "a"

        @provide
        def make_str2(self) -> str:
            return "b"

        @decorate(when=Has(float))
        def decorate_str(self, old_value: str) -> str:
            return old_value + "d"

    with pytest.raises(ImplicitOverrideDetectedError):
        make_container(
            MyProvider(scope=Scope.APP),
            validation_settings=STRICT_VALIDATION,
        )
