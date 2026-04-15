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


def test_decorator_static_evaluation_reuses_cached_value_in_container():
    calls = 0

    class MyProvider(Provider):
        scope = Scope.APP

        @provide(allow_static_evaluation=True)
        def make_str(self) -> str:
            return "a"

        @decorate(allow_static_evaluation=True)
        def decorate_str(self, old_value: str) -> str:
            nonlocal calls
            calls += 1
            return old_value + "d"

        @activate(Marker("A"))
        def is_active(self, decorated: str) -> bool:
            return decorated == "ad"

        @provide(when=Marker("A"))
        def make_int(self) -> int:
            return 1

    container = make_container(MyProvider())

    assert calls == 1
    assert container.get(str) == "ad"
    assert calls == 1
