from contextlib import contextmanager

import click
import pytest
from click.testing import CliRunner

from dishka import FromDishka, make_container
from dishka.integrations.click import inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    AppDep,
    AppMock,
    AppProvider,
)


@contextmanager
def dishka_app(handler, provider):
    command = click.command(inject(handler))
    container = make_container(provider)

    @click.group()
    @click.pass_context
    def main(context: click.Context):
        setup_dishka(
            container=container, context=context, finalize_container=False,
        )

    main.add_command(command, name="test")
    yield main
    container.close()


@contextmanager
def dishka_auto_app(handler, provider):
    command = click.command(handler)
    container = make_container(provider)

    @click.group()
    @click.pass_context
    def main(context: click.Context):
        setup_dishka(
            container=container,
            context=context,
            finalize_container=False,
            auto_inject=True,
        )

    main.add_command(command, name="test")
    yield main
    container.close()


@contextmanager
def dishka_app_with_option(handler, provider):
    command = click.command(click.option("--foo")(inject(handler)))
    container = make_container(provider)

    @click.group()
    @click.pass_context
    def main(context: click.Context):
        setup_dishka(
            container=container, context=context, finalize_container=False,
        )

    main.add_command(command, name="test")
    yield main
    container.close()


@contextmanager
def dishka_nested_group_app(handler, provider):
    command = click.command(handler)
    container = make_container(provider)

    @click.group()
    @click.pass_context
    def main(context: click.Context):
        setup_dishka(
            container=container,
            context=context,
            finalize_container=False,
            auto_inject=True,
        )

    @click.group()
    def group(): ...

    group.add_command(command, name="test")
    main.add_command(group, name="sub")
    yield main
    container.close()


def handle_with_app(
    a: FromDishka[AppDep],
    mock: FromDishka[AppMock],
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
        result = runner.invoke(command, ["test"])
        assert result.exit_code == 0
        app_provider.app_mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called_once()


def test_app_dependency_with_nested_groups(app_provider: AppProvider):
    runner = CliRunner()
    with dishka_nested_group_app(handle_with_app, app_provider) as command:
        result = runner.invoke(command, ["sub", "test"])
        assert result.exit_code == 0
        app_provider.app_mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def handle_with_app_and_option(
    foo: str,
    a: FromDishka[AppDep],
    mock: FromDishka[AppMock],
) -> None:
    mock(a)
    assert foo is not None


def test_app_dependency_with_option(app_provider: AppProvider):
    runner = CliRunner()
    with dishka_app_with_option(
        handle_with_app_and_option,
        app_provider,
    ) as command:
        result = runner.invoke(command, ["test", "--foo", "bar"])
        assert result.exit_code == 0
        app_provider.app_mock.assert_called_with(APP_DEP_VALUE)
        app_provider.request_released.assert_not_called()
