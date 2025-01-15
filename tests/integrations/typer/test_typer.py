from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Annotated, Any

import pytest
import typer
from typer.testing import CliRunner

from dishka import FromDishka, Scope, make_container
from dishka.dependency_source.make_factory import provide
from dishka.integrations.typer import TyperProvider, inject, setup_dishka
from dishka.provider import Provider
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppMock,
    AppProvider,
    RequestDep,
)

AppFactory = Callable[
    [Callable[..., Any], Provider], AbstractContextManager[typer.Typer],
]


class SampleProvider(Provider):

    @provide(scope=Scope.REQUEST)
    def invoked_subcommand(self, context: typer.Context) -> str | None:
        return context.command.name


@contextmanager
def dishka_app(
    handler: Callable[..., Any], provider: Provider,
) -> Iterator[typer.Typer]:
    app = typer.Typer()
    app.command(name="test")(inject(handler))

    container = make_container(provider, SampleProvider(), TyperProvider())
    setup_dishka(container=container, app=app, finalize_container=False)

    yield app
    container.close()


@contextmanager
def dishka_auto_app(
    handler: Callable[..., Any], provider: Provider,
) -> Iterator[typer.Typer]:
    app = typer.Typer()
    app.command(name="test")(handler)

    container = make_container(provider, SampleProvider(), TyperProvider())
    setup_dishka(
        container=container,
        app=app,
        finalize_container=False,
        auto_inject=True,
    )

    yield app
    container.close()


@contextmanager
def dishka_nested_group_app(
    handler: Callable[..., Any], provider: Provider,
) -> Iterator[typer.Typer]:
    app = typer.Typer()
    group = typer.Typer()
    group.command(name="sub")(handler)
    app.add_typer(group, name="test")

    container = make_container(provider, SampleProvider(), TyperProvider())
    setup_dishka(
        container=container,
        app=app,
        finalize_container=False,
        auto_inject=True,
    )

    yield app
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
def test_app_dependency(
    app_provider: AppProvider, app_factory: AppFactory,
) -> None:
    runner = CliRunner()
    with app_factory(handle_with_app, app_provider) as command:
        result = runner.invoke(command, ["test"])
        assert result.exit_code == 0, result.stdout
        app_provider.app_mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called_once()


def test_app_dependency_with_nested_groups(app_provider: AppProvider):
    runner = CliRunner()
    with dishka_nested_group_app(handle_with_app, app_provider) as command:
        result = runner.invoke(command, ["test", "sub"])
        assert result.exit_code == 0
        app_provider.app_mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def handle_with_app_and_options(
    a: FromDishka[AppDep],
    mock: FromDishka[AppMock],
    name: Annotated[str, typer.Argument()] = "Wade",
    surname: Annotated[str | None, typer.Option()] = None,
) -> None:
    mock(a, name, surname)


@pytest.mark.parametrize(
    "app_factory",
    [
        dishka_app,
        dishka_auto_app,
    ],
)
def test_app_dependency_with_option(
    app_provider: AppProvider, app_factory: AppFactory,
) -> None:
    runner = CliRunner()
    with app_factory(handle_with_app_and_options, app_provider) as command:
        result = runner.invoke(command, ["test", "Wade"])
        assert result.exit_code == 0, result.stdout
        app_provider.app_mock.assert_called_with(APP_DEP_VALUE, "Wade", None)
        app_provider.request_released.assert_not_called()


def test_app_dependency_with_nested_groups_and_option(
    app_provider: AppProvider,
) -> None:
    runner = CliRunner()
    with dishka_nested_group_app(
        handle_with_app_and_options, app_provider,
    ) as command:
        result = runner.invoke(
            command, ["test", "sub", "Wade", "--surname", "Wilson"],
        )
        assert result.exit_code == 0, result.stdout
        app_provider.app_mock.assert_called_with(
            APP_DEP_VALUE, "Wade", "Wilson",
        )
        app_provider.request_released.assert_not_called()


def handle_with_context_dependency(
    a: FromDishka[RequestDep],
    mock: FromDishka[AppMock],
    command_name: FromDishka[str | None],
) -> None:
    """Function using a dependency """
    mock(a)
    assert command_name == "test"


def handle_with_context_dependency_and_context_arg(
    ctx_arg: typer.Context,
    a: FromDishka[RequestDep],
    mock: FromDishka[AppMock],
    command_name: FromDishka[str | None],
) -> None:
    mock(a)
    assert command_name == "test"
    assert ctx_arg.command.name == "test"


def handle_with_context_dependency_and_context_kwarg(
    a: FromDishka[RequestDep],
    mock: FromDishka[AppMock],
    command_name: FromDishka[str | None],
    *,
    ctx_kwarg: typer.Context,  # Force as kwargs
) -> None:
    mock(a)
    assert command_name == "test"
    assert ctx_kwarg.command.name == "test"


@pytest.mark.parametrize("app_factory", [dishka_app, dishka_auto_app])
@pytest.mark.parametrize(
    "handler_function", [
        handle_with_context_dependency_and_context_arg,
        handle_with_context_dependency_and_context_kwarg,
        handle_with_context_dependency,
    ],
)
def test_request_dependency_with_context_command(
    app_provider: AppProvider,
    app_factory: AppFactory,
    handler_function: Callable[..., Any],
) -> None:
    runner = CliRunner()
    with app_factory(handler_function, app_provider) as command:
        result = runner.invoke(command, ["test"])
        assert result.exit_code == 0, result.stdout
        app_provider.app_mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
