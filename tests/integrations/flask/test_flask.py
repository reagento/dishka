from contextlib import contextmanager
from typing import Annotated
from unittest.mock import Mock

import pytest
from flask import Flask

from dishka import make_container
from dishka.integrations.flask import FromDishka, inject, setup_dishka
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


@contextmanager
def dishka_auto_app(view, provider):
    app = Flask(__name__)
    app.get("/")(view)
    container = make_container(provider)
    setup_dishka(container=container, app=app, auto_inject=True)
    yield app
    container.close()


def handle_with_app(
        a: Annotated[AppDep, FromDishka()],
        mock: Annotated[Mock, FromDishka()],
) -> None:
    mock(a)


@pytest.mark.parametrize("app_factory", [
    dishka_app, dishka_auto_app,
])
def test_app_dependency(app_provider: AppProvider, app_factory):
    with app_factory(handle_with_app, app_provider) as app:
        app.test_client().get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def handle_with_request(
        a: Annotated[RequestDep, FromDishka()],
        mock: Annotated[Mock, FromDishka()],
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
