"""Integration for Typer https://typer.tiangolo.com"""

__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable
from inspect import Parameter
from typing import Final, ParamSpec, TypeVar, cast, get_type_hints

import click
import typer

from dishka import Container, FromDishka, Scope
from dishka.dependency_source.make_context_var import from_context
from dishka.provider import Provider
from .base import is_dishka_injected, wrap_injection

T = TypeVar("T")
P = ParamSpec("P")
CONTAINER_NAME: Final = "dishka_container"


def inject(func: Callable[P, T]) -> Callable[P, T]:
    # Try to isolate a parameter in the function signature requesting a
    # typer.Context
    hints = get_type_hints(func)
    param_name = next(
        (name for name, hint in hints.items() if hint is typer.Context),
        None,
    )
    if param_name is None:
        # When the handler does not request a typer.Context, we need to add it
        # in our wrapper to be able to inject it in into the container
        def wrapper(context: typer.Context, *args: P.args, **kwargs: P.kwargs) -> T:
            # Inject the typer context into the container
            container: Container = context.meta[CONTAINER_NAME]
            with container({typer.Context: context}, scope=Scope.REQUEST) as new_container:
                context.meta[CONTAINER_NAME] = new_container

                # Then proceed with the regular injection logic
                injected_func = wrap_injection(
                    func=func,
                    container_getter=lambda _, __: click.get_current_context().meta[CONTAINER_NAME],
                    remove_depends=True,
                    is_async=False,
                )
                return injected_func(*args, **kwargs)

        # We reuse the logic of `wrap_injection`, but only to build the expected
        # signature (removing dishka dependencies, adding the typer.Context
        # parameter)
        expected_signature = wrap_injection(
            func=func,
            container_getter=lambda _, __: click.get_current_context().meta[CONTAINER_NAME],
            additional_params=[Parameter(name="context", kind=Parameter.POSITIONAL_ONLY, annotation=typer.Context)],
            remove_depends=True,
            is_async=False,
        )

    else:
        # When the handler requests a typer.Context, we just need to find it and
        # inject
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Get the context from the existing argument
            if param_name in kwargs:
                context: typer.Context = kwargs[param_name]  # type: ignore[assignment]
            else:
                maybe_context = next(
                    # Even though we type `typer.Context`, we get a
                    # `click.Context` instance
                    (arg for arg in args if isinstance(arg, click.Context)), None,
                )
                if maybe_context is None:
                    raise RuntimeError(f"Context argument {param_name} not provided at runtime.")
                context = maybe_context

            # Inject the typer context into the container
            container: Container = context.meta[CONTAINER_NAME]
            with container({typer.Context: context}, scope=Scope.REQUEST) as new_container:
                context.meta[CONTAINER_NAME] = new_container

                # Then proceed with the regular injection logic
                injected_func = wrap_injection(
                    func=func,
                    container_getter=lambda _, __: click.get_current_context().meta[CONTAINER_NAME],
                    remove_depends=True,
                    is_async=False,
                )
                return injected_func(*args, **kwargs)

        # This time, no need to add a parameter to the signature
        expected_signature = wrap_injection(
            func=func,
            container_getter=lambda _, __: get_current_context().meta[CONTAINER_NAME],
            remove_depends=True,
            is_async=False,
        )

    # Copy over all metadata from the expected injected function's signature to
    # our wrapper
    wrapper.__dishka_injected__ = True  # type: ignore[attr-defined]
    wrapper.__name__ = expected_signature.__name__
    wrapper.__qualname__ = expected_signature.__qualname__
    wrapper.__doc__ = expected_signature.__doc__
    wrapper.__module__ = expected_signature.__module__
    wrapper.__annotations__ = expected_signature.__annotations__
    wrapper.__signature__ = expected_signature.__signature__  # type: ignore[attr-defined]

    return cast(Callable[P, T], wrapper)


def _inject_commands(app: typer.Typer) -> None:
    for command in app.registered_commands:
        if command.callback is not None and not is_dishka_injected(
            command.callback,
        ):
            command.callback = inject(command.callback)

    for group in app.registered_groups:
        if group.typer_instance is not None:
            _inject_commands(group.typer_instance)


class TyperProvider(Provider):
    context = from_context(provides=typer.Context, scope=Scope.APP)


def setup_dishka(
    container: Container,
    app: typer.Typer,
    *,
    finalize_container: bool = True,
    auto_inject: bool = False,
) -> None:
    @app.callback()
    def inject_dishka_container(context: typer.Context) -> None:
        context.meta[CONTAINER_NAME] = container

        if finalize_container:
            context.call_on_close(container.close)

    if auto_inject:
        _inject_commands(app)
