from contextlib import contextmanager
from unittest.mock import Mock

import click
import pytest
from click.testing import CliRunner

from dishka import FromDishka, make_container
from dishka.integrations.click import inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


@contextmanager
def dishka_app(handler, provider):
    command = click.command(inject(handler))

    container = make_container(provider)
    setup_dishka(container=container, command=command)
    yield command
    container.close()


@contextmanager
def dishka_auto_app(handler, provider):
    command = click.command(handler)

    container = make_container(provider)
    setup_dishka(container=container, command=command, auto_inject=True)
    yield command
    container.close()


@contextmanager
def dishka_app_with_option(handler, provider):
    command = click.command(click.option("--foo")(inject(handler)))

    container = make_container(provider)
    setup_dishka(container=container, command=command)
    yield command
    container.close()


@contextmanager
def dishka_group_app(handler, provider):
    group = click.group(handler)
    command = click.command(handler)
    group.add_command(command, name="test")

    container = make_container(provider)
    setup_dishka(container=container, command=group, auto_inject=True)
    yield group
    container.close()


@contextmanager
def dishka_nested_group_app(handler, provider):
    group = click.group(handler)
    sub_group = click.group(handler)
    command = click.command(handler)
    sub_group.add_command(command, name="test")
    group.add_command(sub_group, name="sub")

    container = make_container(provider)
    setup_dishka(container=container, command=group, auto_inject=True)
    yield group
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
def test_app_dependency(app_provider: AppProvider, app_factory):
    runner = CliRunner()
    with app_factory(handle_with_app, app_provider) as command:
        result = runner.invoke(command)
        assert result.exit_code == 0
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def test_app_dependency_with_group(app_provider: AppProvider):
    runner = CliRunner()
    with dishka_group_app(handle_with_app, app_provider) as command:
        result = runner.invoke(command, ["test"])
        assert result.exit_code == 0
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def test_app_dependency_with_nested_groups(app_provider: AppProvider):
    runner = CliRunner()
    with dishka_nested_group_app(handle_with_app, app_provider) as command:
        result = runner.invoke(command, ["sub", "test"])
        assert result.exit_code == 0
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def handle_with_request(
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)


def test_request_dependency(app_provider: AppProvider):
    runner = CliRunner()
    with dishka_app(handle_with_request, app_provider) as command:
        result = runner.invoke(command)
        assert result.exit_code == 0
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def test_request_dependency_cache(app_provider: AppProvider):
    runner = CliRunner()
    with dishka_app(handle_with_request, app_provider) as command:
        result = runner.invoke(command)
        assert result.exit_code == 0
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.mock.reset_mock()
        app_provider.request_released.assert_called_once()
        app_provider.request_released.reset_mock()
        result = runner.invoke(command)
        assert result.exit_code == 0
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def handle_with_request_and_option(
    foo: str,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
) -> None:
    mock(a)
    assert foo is not None


def test_request_dependency_with_option(app_provider: AppProvider):
    runner = CliRunner()
    with dishka_app_with_option(
        handle_with_request_and_option, app_provider
    ) as command:
        result = runner.invoke(command, ["--foo", "bar"])
        assert result.exit_code == 0
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
