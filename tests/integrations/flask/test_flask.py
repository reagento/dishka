from contextlib import contextmanager
from typing import Annotated
from unittest.mock import Mock

from flask import Flask

from dishka import make_container
from dishka.integrations.flask import Depends, inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


@contextmanager
def dishka_app(view, provider):
    app = Flask(__name__)
    app.get("/")(inject(view))
    container = make_container(provider)
    setup_dishka(container=container, app=app)
    yield app
    container.close()


def handle_with_app(
    a: Annotated[AppDep, Depends()],
    mock: Annotated[Mock, Depends()],
) -> None:
    mock(a)


def test_app_dependency(app_provider: AppProvider):
    with dishka_app(handle_with_app, app_provider) as app:
        app.test_client().get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def handle_with_request(
    a: Annotated[RequestDep, Depends()],
    mock: Annotated[Mock, Depends()],
) -> None:
    mock(a)


def test_request_dependency(app_provider: AppProvider):
    with dishka_app(handle_with_request, app_provider) as app:
        app.test_client().get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def test_request_dependency2(app_provider: AppProvider):
    with dishka_app(handle_with_request, app_provider) as app:
        app.test_client().get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()
        app.test_client().get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
