import pytest

from dishka import Marker, Provider, Scope, make_container, provide
from dishka.exception_base import InvalidMarkerError
from dishka.exceptions import NoActivatorError


class ServiceA:
    pass


class ServiceB:
    pass


class Service:
    pass


def test_no_activator_error_shows_requesting_factories():
    class MyProvider(Provider):
        scope = Scope.REQUEST

        @provide(when=Marker("unregistered"))
        def service_a(self) -> ServiceA:
            return ServiceA()

        @provide(when=Marker("unregistered"))
        def service_b(self) -> ServiceB:
            return ServiceB()

    with pytest.raises(NoActivatorError) as exc_info:
        make_container(MyProvider())

    error_msg = str(exc_info.value)
    assert "unregistered" in error_msg
    assert "service_a" in error_msg
    assert "service_b" in error_msg
    assert "Used in:" in error_msg


def test_no_activator_error_shows_when_expression():
    class MyProvider(Provider):
        scope = Scope.REQUEST

        @provide(when=Marker("unregistered"))
        def service(self) -> ServiceA:
            return ServiceA()

    with pytest.raises(NoActivatorError) as exc_info:
        make_container(MyProvider())

    error_msg = str(exc_info.value)
    assert "Marker('unregistered')" in error_msg
    assert "service:" in error_msg


def test_invalid_marker_error_shows_factory():
    class MyProvider(Provider):
        scope = Scope.REQUEST

        @provide(when="not_a_marker")
        def broken_service(self) -> Service:
            return Service()

    with pytest.raises(InvalidMarkerError) as exc_info:
        make_container(MyProvider())

    error_msg = str(exc_info.value)
    assert "'not_a_marker'" in error_msg
    assert "broken_service" in error_msg
    assert "Used in:" in error_msg
