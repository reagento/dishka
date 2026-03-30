from typing import NewType

import pytest

from dishka import Marker, Provider, Scope, make_container
from dishka.exception_base import InvalidMarkerError
from dishka.exceptions import (
    ActivatorOverrideError,
    NoActivatorError,
    NoFactoryError,
    WhenOverrideConflictError,
)


def is_zero(value: int) -> bool:
    return value == 0


def fallback() -> str:
    return "a"


def needs_float(value: float) -> str:
    return str(value)


@pytest.mark.parametrize( ("number", "expected", "raises"), [
    (1, "a", False),
    (0, None, True),
])
def test_unresolved_conditional_branch_is_validated_at_runtime(
    *,
    number: int,
    expected: str | None,
    raises: bool,
):
    provider = Provider(scope=Scope.APP)
    provider.activate(is_zero, Marker("ZERO"))
    provider.provide(lambda: number, provides=int)
    provider.provide(fallback, provides=str)
    provider.provide(needs_float, provides=str, when=Marker("ZERO"))
    container = make_container(provider)
    if raises:
        with pytest.raises(NoFactoryError):
            container.get(str)
    else:
        assert container.get(str) == expected


@pytest.mark.parametrize(("value", "b_is_active"), [
    ("a", False),
    ("b", True),
])
def test_when_active(*, value: str, b_is_active: bool):
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str)  # default
    provider.provide(lambda: "b", provides=str, when=Marker("B"))
    provider.activate(lambda: b_is_active, Marker("B"))

    c = make_container(provider)
    assert c.get(str) == value


@pytest.mark.parametrize("value", ["a", "b"])
def test_when_type(value: str):
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str, when=Marker("a"))
    provider.provide(lambda: "b", provides=str, when=Marker("b"))

    def activator(marker: Marker) -> bool:
        return marker.value == value

    provider.activate(activator, Marker)

    c = make_container(provider)
    assert c.get(str) == value


@pytest.mark.parametrize("value", ["a", "b"])
def test_when_type_nested_scope(value: str):
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(lambda: "a", provides=str, when=Marker("a"))
    provider.provide(lambda: "b", provides=str, when=Marker("b"))

    def activator(marker: Marker) -> bool:
        return marker.value == value

    provider.activate(activator, Marker)

    c = make_container(provider)
    with c() as request_c:
        assert request_c.get(str) == value


def test_when_dependencies():
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(lambda: "a", provides=str, when=Marker("1"))
    provider.provide(lambda: "b", provides=str, when=Marker("2"))
    provider.provide(lambda: 2, provides=int)

    def activator(marker: Marker, number: int) -> bool:
        return marker.value == str(number)

    provider.activate(activator, Marker)

    c = make_container(provider)
    with c() as request_c:
        assert request_c.get(str) == "b"


def test_when_and_override():
    provider = Provider(scope=Scope.REQUEST)
    with pytest.raises(WhenOverrideConflictError):
        provider.provide(str, when=Marker("a"), override=True)


def test_unregistered_activator():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "x", provides=str, when=Marker("1"))
    with pytest.raises(NoActivatorError):
        make_container(provider)


def test_invalid_marker():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "x", provides=str, when="Hello")
    with pytest.raises(InvalidMarkerError):
        make_container(provider)


def test_activator_override():
    provider = Provider(scope=Scope.APP)
    provider.activate(lambda: True, Marker("B"))
    provider.activate(lambda: True, Marker("B"))
    with pytest.raises(ActivatorOverrideError):
        make_container(provider)


def provide_with_dep(a: float) -> str:
    return str(a)


def test_has_no_dep_inactive():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str)
    provider.activate(lambda: False, Marker("B"))
    provider.provide(provide_with_dep, provides=str, when=Marker("B"))

    c = make_container(provider)
    assert c.get(str) == "a"


def test_has_no_dep_active():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str)
    provider.activate(lambda: True, Marker("B"))
    provider.provide(provide_with_dep, provides=str, when=Marker("B"))

    with pytest.raises(NoFactoryError):
        make_container(provider)


def activate_zero(value: int):
    return value == 0


def test_activation_with_param_static_inactive():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str)
    provider.activate(activate_zero, Marker("ZERO"))
    provider.provide(provide_with_dep, provides=str, when=Marker("ZERO"))
    c = make_container(provider, context={int: 1})
    assert c.get(str) == "a"


def test_activation_with_param_static_active_no_dep():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str)
    provider.activate(activate_zero, Marker("ZERO"))
    provider.provide(provide_with_dep, provides=str, when=Marker("ZERO"))
    with pytest.raises(NoFactoryError):
        make_container(provider, context={int: 0})


@pytest.mark.parametrize(("number", "string"), [
    (0, "b"),
    (1, "a"),
])
def test_activation_with_param_dynamic(number, string):
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(lambda: "a", provides=str)
    provider.provide(lambda: "b", provides=str, when=Marker("ZERO"))
    provider.from_context(int)
    provider.activate(activate_zero, Marker("ZERO"))
    c = make_container(provider)
    with c({int: number}) as request_c:
        assert request_c.get(str) == string


def test_activation_with_selector_alias_inactive():
    int1 = NewType("int1", int)
    int2 = NewType("int2", int)
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str)
    provider.provide(provide_with_dep, provides=str, when=Marker("ZERO"))
    provider.activate(lambda: True, Marker("another"))
    provider.alias(int1, provides=int)
    provider.alias(int2, provides=int, when=Marker("another"))
    provider.activate(activate_zero, Marker("ZERO"))
    c = make_container(provider, context={int1: 1, int2: 2})
    assert c.get(str) == "a"
