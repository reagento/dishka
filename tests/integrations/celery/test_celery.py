from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import Mock

from celery import Celery

from dishka import FromDishka, Provider, make_container
from dishka.integrations.celery import DishkaTask, inject, setup_dishka
from ..common import APP_DEP_VALUE, AppDep, AppProvider


@contextmanager
def dishka_app(provider: Provider) -> Iterator[Celery]:
    app = Celery()
    container = make_container(provider)
    setup_dishka(container=container, app=app)
    yield app
    container.close()


@contextmanager
def dishka_auto_app(provider: Provider) -> Iterator[Celery]:
    app = Celery(task_cls=DishkaTask)
    container = make_container(provider)
    setup_dishka(container=container, app=app)
    yield app
    container.close()


def handle_with_app(
    a: FromDishka[AppDep],
    mock: FromDishka[Mock],
) -> AppDep:
    mock(a)
    return a


def test_app_dependency(app_provider: AppProvider):
    with dishka_auto_app(app_provider) as app:
        task = app.task(inject(handle_with_app))
        result = task.apply()

        assert result.get() == APP_DEP_VALUE
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def test_app_auto_dependency(app_provider: AppProvider):
    with dishka_auto_app(app_provider) as app:
        task = app.task(handle_with_app)

        result = task.apply()

        assert result.get() == APP_DEP_VALUE
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()
