from collections.abc import (
    Awaitable,
    Callable,
    Sequence,
)
from inspect import (
    Parameter,
    Signature,
    _ParameterKind,
    signature,
)
from typing import (
    Annotated,
    Any,
    Literal,
    ParamSpec,
    TypeAlias,
    TypeVar,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from dishka.async_container import AsyncContainer
from dishka.code_tools.inject_compiler import (
    InjectedFuncType,
    compile_injected_func,
)
from dishka.container import Container
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.depends_marker import FromDishka
from dishka.entities.key import DependencyKey, _FromComponent
from dishka.entities.scope import Scope

T = TypeVar("T")
P = ParamSpec("P")
DependencyParser: TypeAlias = Callable[[Parameter, Any], DependencyKey | None]
ContainerGetter: TypeAlias = Callable[[tuple[Any, ...], dict[str, Any]], T]
ProvideContext: TypeAlias = Callable[
    [tuple[Any, ...], dict[str, Any]],
    dict[Any, Any],
]
DependsClass: TypeAlias = cast(
    type | Sequence[type],
    FromDishka | _FromComponent,
)
InjectFunc: TypeAlias = Callable[[Callable[P, T]], Callable[P, T]]


def default_parse_dependency(
    parameter: Parameter,
    hint: Any,
) -> DependencyKey | None:
    """Resolve dependency type or return None if it is not a dependency."""
    if get_origin(hint) is not Annotated:
        return None
    args = get_args(hint)
    dep = next(
        (arg for arg in args if isinstance(arg, DependsClass)),
        None,
    )
    if not dep:
        return None
    if isinstance(dep, FromDishka | _FromComponent):  # type: ignore[arg-type]
        return DependencyKey(args[0], dep.component)
    else:
        return DependencyKey(args[0], DEFAULT_COMPONENT)


@overload
def wrap_injection(
    *,
    func: Callable[P, T],
    container_getter: ContainerGetter[Container],
    is_async: Literal[False] = False,
    remove_depends: bool = True,
    additional_params: Sequence[Parameter] = (),
    parse_dependency: DependencyParser = default_parse_dependency,
    manage_scope: bool = False,
    provide_context: ProvideContext | None = None,
    scope: Scope | None = None,
) -> Callable[P, T]: ...


@overload
def wrap_injection(
    *,
    func: Callable[P, T],
    container_getter: ContainerGetter[AsyncContainer],
    is_async: Literal[True],
    remove_depends: bool = True,
    additional_params: Sequence[Parameter] = (),
    parse_dependency: DependencyParser = default_parse_dependency,
    manage_scope: bool = False,
    provide_context: ProvideContext | None = None,
    scope: Scope | None = None,
) -> Callable[P, T]: ...


def wrap_injection(
    *,
    func: Callable[P, T],
    container_getter: ContainerGetter[Container | AsyncContainer],
    is_async: bool = False,
    remove_depends: bool = True,
    additional_params: Sequence[Parameter] = (),
    parse_dependency: DependencyParser = default_parse_dependency,
    manage_scope: bool = False,
    scope: Scope | None = None,
    provide_context: ProvideContext | None = None,
) -> Callable[P, T]:
    hints = get_type_hints(func, include_extras=True)
    func_signature = signature(func)

    dependencies = {}
    for name, param in func_signature.parameters.items():
        hint = hints.get(name, Any)
        dep = parse_dependency(param, hint)
        if dep is None:
            continue
        dependencies[name] = dep

    if not dependencies:
        try:
            func.__dishka_injected__ = True  # type: ignore[attr-defined]
        except AttributeError:
            pass
        else:
            return func

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
        new_params = list(func_signature.parameters.values())
    # fix hints
    new_params = [
        param.replace(annotation=hints.get(param.name, param.annotation))
        for param in new_params
    ]

    auto_injected_func: Callable[P, T | Awaitable[T]]
    if additional_params:
        new_params = _add_params(new_params, additional_params)
        for param in additional_params:
            new_annotations[param.name] = param.annotation

    if is_async:
        func = cast(Callable[P, Awaitable[T]], func)
        container_getter = cast(
            ContainerGetter[AsyncContainer],
            container_getter,
        )
    else:
        container_getter = cast(
            ContainerGetter[Container],
            container_getter,
        )

    injected_func_type = InjectedFuncType.get_injected_func_type(
        func,
        is_async_container=is_async,
        manage_scope=manage_scope,
        scope=scope,
        provide_context=provide_context,
    )

    auto_injected_func = compile_injected_func(
        injected_func_type,
        func=func,
        provide_context=provide_context,
        dependencies=dependencies,
        additional_params=additional_params,
        container_getter=container_getter,
        scope=scope,
    )

    auto_injected_func.__dishka_orig_func__ = func  # type: ignore[attr-defined]
    auto_injected_func.__dishka_injected__ = True  # type: ignore[attr-defined]
    auto_injected_func.__name__ = func.__name__
    auto_injected_func.__qualname__ = func.__qualname__
    auto_injected_func.__doc__ = func.__doc__
    auto_injected_func.__module__ = func.__module__
    auto_injected_func.__annotations__ = new_annotations
    auto_injected_func.__signature__ = Signature(  # type: ignore[attr-defined]
        parameters=new_params,
        return_annotation=func_signature.return_annotation,
    )
    return cast(Callable[P, T], auto_injected_func)


def is_dishka_injected(func: Callable[..., Any]) -> bool:
    return hasattr(func, "__dishka_injected__")


def _add_params(
    params: Sequence[Parameter],
    additional_params: Sequence[Parameter],
):
    params_kind_dict: dict[_ParameterKind, list[Parameter]] = {}

    for param in params:
        params_kind_dict.setdefault(param.kind, []).append(param)

    for param in additional_params:
        params_kind_dict.setdefault(param.kind, []).append(param)

    var_positional = params_kind_dict.get(Parameter.VAR_POSITIONAL, [])
    if len(var_positional) > 1:
        param_names = (param.name for param in var_positional)
        var_positional_names = ", *".join(param_names)
        base_msg = "more than one variadic positional parameter: *"
        msg = base_msg + var_positional_names
        raise ValueError(msg)

    var_keyword = params_kind_dict.get(Parameter.VAR_KEYWORD, [])
    if len(var_keyword) > 1:
        var_keyword_names = ", **".join(param.name for param in var_keyword)
        msg = "more than one variadic keyword parameter: " + var_keyword_names
        raise ValueError(msg)

    positional_only = params_kind_dict.get(Parameter.POSITIONAL_ONLY, [])
    positional_or_keyword = params_kind_dict.get(
        Parameter.POSITIONAL_OR_KEYWORD,
        [],
    )
    keyword_only = params_kind_dict.get(Parameter.KEYWORD_ONLY, [])

    result_params = []
    result_params.extend(positional_only)
    result_params.extend(positional_or_keyword)
    result_params.extend(var_positional)
    result_params.extend(keyword_only)
    result_params.extend(var_keyword)

    return result_params
