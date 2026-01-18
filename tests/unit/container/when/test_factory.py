import pytest

from dishka import Marker, Provider, Scope, make_container
from dishka.exceptions import InvalidMarkerError, NoActivatorError


@pytest.mark.parametrize(("value", "b_is_active"), [
    ("a", False),
    ("b", True),
])
def test_when_active(*, value: str, b_is_active: bool):
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str)  # default
    provider.provide(lambda: "b", provides=str, when=Marker("B"))
    provider.activator(lambda: b_is_active, Marker("B"))

    c = make_container(provider)
    assert c.get(str) == value


@pytest.mark.parametrize("value", ["a", "b"])
def test_when_type(value: str):
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str, when=Marker("a"))
    provider.provide(lambda: "b", provides=str, when=Marker("b"))

    def activator(marker: Marker) -> bool:
        return marker.value == value

    provider.activator(activator, Marker)

    c = make_container(provider)
    assert c.get(str) == value


@pytest.mark.parametrize("value", ["a", "b"])
def test_when_type_nested_scope(value: str):
    provider = Provider(scope=Scope.REQUEST)
    provider.provide(lambda: "a", provides=str, when=Marker("a"))
    provider.provide(lambda: "b", provides=str, when=Marker("b"))

    def activator(marker: Marker) -> bool:
        return marker.value == value

    provider.activator(activator, Marker)

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

    provider.activator(activator, Marker)

    c = make_container(provider)
    with c() as request_c:
        assert request_c.get(str) == "b"


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
