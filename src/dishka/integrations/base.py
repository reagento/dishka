from collections.abc import Awaitable, Callable, Sequence
from inspect import Parameter, Signature, signature
from typing import (
    Annotated,
    Any,
    Literal,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from dishka.async_container import AsyncContainer
from dishka.container import Container
from dishka.entities.depends_marker import FromDishka
from dishka.entities.key import DEFAULT_COMPONENT, DependencyKey, FromComponent


def default_parse_dependency(
        parameter: Parameter,
        hint: Any,
        depends_class: type | Sequence[type] = (FromDishka, FromComponent),
) -> Any:
    """Resolve dependency type or return None if it is not a dependency."""
    if get_origin(hint) is not Annotated:
        return None
    args = get_args(hint)
    dep = next(
        (arg for arg in args if isinstance(arg, depends_class)),
        None,
    )
    if not dep:
        return None
    if isinstance(dep, (FromDishka, FromComponent)):
        return DependencyKey(args[0], dep.component)
    else:
        return DependencyKey(args[0], DEFAULT_COMPONENT)


DependencyParser = Callable[[Parameter, Any], DependencyKey | None]


@overload
def wrap_injection(
        *,
        func: Callable,
        container_getter: Callable[[tuple, dict], Container],
        is_async: Literal[False] = False,
        remove_depends: bool = True,
        additional_params: Sequence[Parameter] = (),
        parse_dependency: DependencyParser = default_parse_dependency,
) -> Callable:
    ...


@overload
def wrap_injection(
        *,
        func: Callable,
        container_getter: Callable[[tuple, dict], AsyncContainer],
        is_async: Literal[True],
        remove_depends: bool = True,
        additional_params: Sequence[Parameter] = (),
        parse_dependency: DependencyParser = default_parse_dependency,
) -> Awaitable:
    ...


def wrap_injection(
        *,
        func: Callable,
        container_getter: Callable,
        is_async: bool = False,
        remove_depends: bool = True,
        additional_params: Sequence[Parameter] = (),
        parse_dependency: DependencyParser = default_parse_dependency,
):
    hints = get_type_hints(func, include_extras=True)
    func_signature = signature(func)

    dependencies = {}
    for name, param in func_signature.parameters.items():
        hint = hints.get(name, Any)
        dep = parse_dependency(param, hint)
        if dep is None:
            continue
        dependencies[name] = dep

    if remove_depends:
        new_annotations = {
            name: hint
            for name, hint in hints.items()
            if name not in dependencies
        }
        new_params = [
            param
            for name, param in func_signature.parameters.items()
            if name not in dependencies
        ]
    else:
        new_annotations = hints.copy()
        new_params = func_signature.parameters.copy()

    if additional_params:
        new_params.extend(additional_params)
        for param in additional_params:
            new_annotations[param.name] = param.annotation

    if is_async:
        autoinjected_func = _async_injection_wrapper(
            container_getter=container_getter,
            dependencies=dependencies,
            func=func,
            additional_params=additional_params,
        )
    else:
        autoinjected_func = _sync_injection_wrapper(
            container_getter=container_getter,
            dependencies=dependencies,
            func=func,
            additional_params=additional_params,
        )

    autoinjected_func.__dishka_injected__ = True
    autoinjected_func.__name__ = func.__name__
    autoinjected_func.__qualname__ = func.__qualname__
    autoinjected_func.__doc__ = func.__doc__
    autoinjected_func.__annotations__ = new_annotations
    autoinjected_func.__signature__ = Signature(
        parameters=new_params,
        return_annotation=func_signature.return_annotation,
    )
    return autoinjected_func


def is_dishka_injected(func):
    return hasattr(func, "__dishka_injected__")


def _async_injection_wrapper(
        container_getter: Callable,
        additional_params: Sequence[Parameter],
        dependencies: dict[str, DependencyKey],
        func: Callable,
):
    async def autoinjected_func(*args, **kwargs):
        container = container_getter(args, kwargs)
        for param in additional_params:
            kwargs.pop(param.name)
        solved = {
            name: await container.get(dep.type_hint, component=dep.component)
            for name, dep in dependencies.items()
        }
        return await func(*args, **kwargs, **solved)

    return autoinjected_func


def _sync_injection_wrapper(
        container_getter: Callable,
        additional_params: Sequence[Parameter],
        dependencies: dict[str, DependencyKey],
        func: Callable,
):
    def autoinjected_func(*args, **kwargs):
        container = container_getter(args, kwargs)
        for param in additional_params:
            kwargs.pop(param.name)
        solved = {
            name: container.get(dep.type_hint, component=dep.component)
            for name, dep in dependencies.items()
        }
        return func(*args, **kwargs, **solved)

    return autoinjected_func
