from collections.abc import Callable, Generator, Iterable
from contextlib import AbstractContextManager, contextmanager
from typing import Any, Literal, TypeAlias
from unittest.mock import Mock

import pytest
from flask import Flask, g
from flask.typing import (
    BeforeRequestCallable,
)

from dishka import Provider, make_container
from dishka.integrations.flask import FromDishka, inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)

AppFactory: TypeAlias = Callable[
    ...,
    AbstractContextManager[Flask],
]


@contextmanager
def dishka_app(
    view: Callable[..., Any],
    provider: Provider,
) -> Generator[Flask, None, None]:
    app = Flask(__name__)
    app.get("/")(inject(view))
    container = make_container(provider)
    setup_dishka(container=container, app=app)
    yield app
    container.close()


@contextmanager
def dishka_auto_app(
    view: Callable[..., Any],
    provider: Provider,
) -> Generator[Flask, None, None]:
    app = Flask(__name__)
    app.get("/")(view)
    container = make_container(provider)
    setup_dishka(container=container, app=app, auto_inject=True)
    yield app
    container.close()


@contextmanager
def dishka_app_with_lifecycle_hooks(
    view: Callable[..., Any],
    provider: Provider,
    *,
    before_request: Iterable[BeforeRequestCallable] | None = None,
) -> Generator[Flask, None, None]:
    app = Flask(__name__)
    if before_request is not None:
        for func in before_request:
            app.before_request(func)

    app.get("/")(view)
    container = make_container(provider)
    setup_dishka(container=container, app=app, auto_inject=True)
    yield app
    container.close()


def handle_with_app(
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


@pytest.mark.parametrize(
    "app_factory",
    [
        dishka_app,
        dishka_auto_app,
    ],
)
def test_app_dependency(
    app_provider: AppProvider,
    app_factory: AppFactory,
) -> None:
    with app_factory(handle_with_app, app_provider) as app:
        app.test_client().get("/")
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def handle_with_request(
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


def test_request_dependency(app_provider: AppProvider) -> None:
    with dishka_app(handle_with_request, app_provider) as app:
        app.test_client().get("/")
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def test_request_dependency2(app_provider: AppProvider) -> None:
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


def test_before_request_adds_container_to_flask_g(
    app_provider: AppProvider,
) -> None:
    with (
        dishka_app(
            handle_with_request,
            app_provider,
        ) as app,
        app.test_request_context(),
    ):
        app.test_client().get("/")
        assert hasattr(g, "dishka_container")


def before_request_interceptor(*args, **kwargs) -> Literal["OK"]:
    return "OK"


def test_teardown_skips_container_close_when_not_in_flask_g(
    app_provider: AppProvider,
) -> None:
    with (
        dishka_app_with_lifecycle_hooks(
            handle_with_request,
            app_provider,
            before_request=(before_request_interceptor,),
        ) as app,
        app.test_request_context(),
    ):
        app.test_client().get("/")
        assert not hasattr(g, "dishka_container")
