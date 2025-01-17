from collections.abc import Iterator
from contextlib import contextmanager
from unittest.mock import Mock

from celery import Celery, Task

from dishka import FromDishka, Provider, make_container
from dishka.integrations.celery import DishkaTask, inject, setup_dishka
from ..common import APP_DEP_VALUE, AppDep, AppProvider


@contextmanager
def dishka_app(provider: Provider) -> Iterator[Celery]:
    app = Celery()
    app.conf["task_always_eager"] = True
    container = make_container(provider)
    setup_dishka(container=container, app=app)
    yield app
    container.close()


@contextmanager
def dishka_auto_app(provider: Provider) -> Iterator[Celery]:
    app = Celery(task_cls=DishkaTask)
    app.conf["task_always_eager"] = True
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


def handle_with_bind(
    task: Task,
    mock: FromDishka[Mock],
):
    mock(task)


def handle_with_args(*args, mock: FromDishka[Mock]):
    mock(args)


def handle_with_kwargs(
    mock: FromDishka[Mock],
    **kwargs,
):
    mock(kwargs)


def handle_with_keyword_only(*, x: int, mock: FromDishka[Mock]):
    mock(x)


def test_app_dependency(app_provider: AppProvider):
    with dishka_app(app_provider) as app:
        task = app.task(inject(handle_with_app))
        result = task.delay()

        assert result.get() == APP_DEP_VALUE
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def test_app_auto_dependency(app_provider: AppProvider):
    with dishka_auto_app(app_provider) as app:
        task = app.task(handle_with_app)

        result = task.delay()

        assert result.get() == APP_DEP_VALUE
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def test_with_bind(app_provider: AppProvider):
    with dishka_app(app_provider) as app:
        task = app.task(bind=True)(inject(handle_with_bind))
        result = task.delay()

        result.get()
        app_provider.mock.assert_called_with(task)


def test_with_bind_auto(app_provider: AppProvider):
    with dishka_auto_app(app_provider) as app:
        task = app.task(bind=True)(handle_with_bind)

        result = task.delay()

        result.get()
        app_provider.mock.assert_called_with(task)


def test_with_args(app_provider: AppProvider):
    args = (5, 6)

    with dishka_app(app_provider) as app:
        task = app.task(inject(handle_with_args))
        result = task.delay(*args)

        result.get()
        app_provider.mock.assert_called_with(args)


def test_with_args_auto(app_provider: AppProvider):
    args = (5, 6)

    with dishka_auto_app(app_provider) as app:
        task = app.task(handle_with_args)

        result = task.delay(*args)

        result.get()
        app_provider.mock.assert_called_with(args)


def test_with_kwargs(app_provider: AppProvider):
    kwargs = {"x": 5, "y": 6}

    with dishka_app(app_provider) as app:
        task = app.task(inject(handle_with_kwargs))
        result = task.delay(**kwargs)

        result.get()
        app_provider.mock.assert_called_with(kwargs)


def test_with_kwargs_auto(app_provider: AppProvider):
    kwargs = {"x": 5, "y": 6}

    with dishka_auto_app(app_provider) as app:
        task = app.task(handle_with_kwargs)

        result = task.delay(**kwargs)

        result.get()
        app_provider.mock.assert_called_with(kwargs)


def test_with_keyword_only(app_provider: AppProvider):
    keyword = {"x": 6}
    with dishka_app(app_provider) as app:
        task = app.task(inject(handle_with_keyword_only))
        result = task.delay(**keyword)

        result.get()
        app_provider.mock.assert_called_with(keyword.get("x"))


def test_with_keyword_only_only_auto(app_provider: AppProvider):
    keyword = {"x": 6}
    with dishka_auto_app(app_provider) as app:
        task = app.task(handle_with_keyword_only)

        result = task.delay(**keyword)

        result.get()
        app_provider.mock.assert_called_with(keyword.get("x"))
