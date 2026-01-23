from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any
from unittest.mock import Mock

import pytest
from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.response import Response
from pyramid.testing import DummyRequest

from dishka import FromDishka, Provider, Scope, make_container, provide
from dishka.integrations.pyramid import (
    CONTAINER_NAME,
    CONTAINER_WRAPPER_NAME,
    PyramidProvider,
    inject,
    setup_dishka,
)
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


@contextmanager
def dishka_app(
    view: Callable[..., Any],
    provider: Provider,
) -> Generator[Configurator, None, None]:
    config = Configurator()
    container = make_container(provider)
    setup_dishka(container, config)

    yield config

    container.close()


def call_view_with_container(
    view: Callable,
    config: Configurator,
    request: type[Request] = Request,
) -> Any:
    container = config.registry[CONTAINER_WRAPPER_NAME]
    request = DummyRequest()

    with container(context={request: request}) as request_container:
        setattr(request, CONTAINER_NAME, request_container)
        return view(request)


def handle_with_app(
    request,
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> Response:
    mock(a)
    return Response("OK")


def test_app_dependency(app_provider: AppProvider) -> None:
    with dishka_app(handle_with_app, app_provider) as config:
        view = inject(handle_with_app)
        response = call_view_with_container(view, config)

        assert response.status == "200 OK"
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()

    app_provider.app_released.assert_called()


def handle_with_request(
    request,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> Response:
    mock(a)
    return Response("OK")


def test_request_dependency(app_provider: AppProvider) -> None:
    with dishka_app(handle_with_request, app_provider) as config:
        view = inject(handle_with_request)
        response = call_view_with_container(view, config)

        assert response.status == "200 OK"
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def test_request_dependency_multiple_requests(
    app_provider: AppProvider,
) -> None:
    with dishka_app(handle_with_request, app_provider) as config:
        view = inject(handle_with_request)

        response = call_view_with_container(view, config)

        assert response.status == "200 OK"
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

        app_provider.mock.reset_mock()
        app_provider.request_released.reset_mock()

        response = call_view_with_container(view, config)

        assert response.status == "200 OK"
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def test_multiple_views_with_injection(app_provider: AppProvider) -> None:
    def view1(
        request,
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
    ) -> Response:
        mock(a)
        return Response("view1")

    def view2(
        request,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
    ) -> Response:
        mock(a)
        return Response("view2")

    config = Configurator()
    container = make_container(app_provider)
    setup_dishka(container, config)

    injected_view1 = inject(view1)
    injected_view2 = inject(view2)

    response = call_view_with_container(injected_view1, config)
    assert response.text == "view1"

    response = call_view_with_container(injected_view2, config)
    assert response.text == "view2"

    assert app_provider.mock.call_count == 2

    container.close()


def test_inject_without_dishka_params(app_provider: AppProvider) -> None:
    def simple_view(request) -> Response:
        return Response("OK")

    config = Configurator()
    container = make_container(app_provider)
    setup_dishka(container, config)

    view = inject(simple_view)
    response = call_view_with_container(view, config)

    assert response.status == "200 OK"
    assert response.text == "OK"

    container.close()


def test_pyramid_provider_injects_request() -> None:
    class ServiceWithRequest(Provider):
        @provide(scope=Scope.REQUEST)
        def get_value(self, request: Request) -> str:
            return f"path:{request.path}"

    def view_with_request_in_service(
        request,
        value: FromDishka[str],
    ) -> Response:
        return Response(value)

    config = Configurator()
    container = make_container(PyramidProvider(), ServiceWithRequest())
    setup_dishka(container, config)

    request = DummyRequest(path="/test-path")

    with container(context={Request: request}) as request_container:
        setattr(request, CONTAINER_NAME, request_container)

        view = inject(view_with_request_in_service)
        response = view(request)

        assert response.status == "200 OK"
        assert response.text == "path:/test-path"

    container.close()


def test_error_handling_closes_container(app_provider: AppProvider) -> None:
    def failing_view(
        request,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
    ) -> Response:
        mock(a)
        raise ValueError("Test error")

    with dishka_app(failing_view, app_provider) as config:
        view = inject(failing_view)

        with pytest.raises(ValueError, match="Test error"):
            call_view_with_container(view, config)

        app_provider.request_released.assert_called_once()


def test_container_not_found_raises_error() -> None:
    def view_needing_container(request, a: FromDishka[RequestDep]) -> Response:
        return Response("OK")

    view = inject(view_needing_container)
    request = DummyRequest()

    with pytest.raises(AttributeError):
        view(request)
