from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass
from enum import Enum
from inspect import (
    Parameter,
    isasyncgenfunction,
    iscoroutinefunction,
    isgeneratorfunction,
)
from typing import Any, ParamSpec, TypeAlias, TypeVar

from dishka.async_container import AsyncContainer
from dishka.entities.key import DependencyKey
from dishka.entities.scope import Scope
from dishka.integrations.exceptions import (
    ImproperProvideContextUsageError,
    InvalidInjectedFuncTypeError,
)
from .code_builder import CodeBuilder

T = TypeVar("T")
P = ParamSpec("P")
ContainerGetter: TypeAlias = Callable[[tuple[Any, ...], dict[str, Any]], T]
ProvideContext: TypeAlias = Callable[
    [tuple[Any, ...], dict[str, Any]],
    dict[Any, Any],
]
InjectFunc: TypeAlias = Callable[[Callable[P, T]], Callable[P, T]]


class FunctionType(Enum):
    GENERATOR = "generator"
    CALLABLE = "callable"


@dataclass(frozen=True, slots=True, kw_only=True)
class InjectedFuncType:
    is_async_container: bool
    manage_scope: bool
    is_async_func: bool
    func_type: FunctionType

    def __post_init__(self) -> None:
        if self.is_async_container and not self.is_async_func:
            raise InvalidInjectedFuncTypeError

    @classmethod
    def get_injected_func_type(
        cls,
        func: Callable[P, T],
        *,
        is_async_container: bool,
        manage_scope: bool,
        scope: Scope | None,
        provide_context: ProvideContext | None,
    ) -> "InjectedFuncType":
        if isasyncgenfunction(func):
            func_type = FunctionType.GENERATOR
            is_async = True
        elif isgeneratorfunction(func):
            func_type = FunctionType.GENERATOR
            is_async = False
        elif iscoroutinefunction(func):
            func_type = FunctionType.CALLABLE
            is_async = True
        else:
            func_type = FunctionType.CALLABLE
            is_async = False

        manage_scope = manage_scope or bool(scope)

        if not manage_scope and provide_context is not None:
            raise ImproperProvideContextUsageError

        return cls(
            is_async_container=is_async_container,
            manage_scope=manage_scope,
            is_async_func=is_async,
            func_type=func_type,
        )


def compile_injected_func(
    injected_func_type: InjectedFuncType,
    container_getter: ContainerGetter[AsyncContainer],
    additional_params: Sequence[Parameter],
    dependencies: dict[str, DependencyKey],
    func: Callable[P, T],
    provide_context: ProvideContext | None = None,
    scope: Scope | None = None,
) -> InjectFunc[P, T]:
    builder = CodeBuilder(is_async=injected_func_type.is_async_func)

    original_func_name = builder.global_(func, "func_" + func.__name__)
    injected_func_name = "dishka_" + original_func_name

    with builder.def_(
        name=injected_func_name,
        args=["*args", "**kwargs"],
    ):
        container_getter_name = builder.global_(
            container_getter,
            "container_getter",
        )

        builder.assign_local(
            "container",
            builder.call(
                container_getter_name,
                "args",
                "kwargs",
            ),
        )

        for param in additional_params:
            builder.statement(f"kwargs.pop('{param.name}')")

        context: AbstractContextManager[None] = nullcontext()

        if injected_func_type.manage_scope:
            if provide_context is not None:
                provide_context_name = builder.global_(
                    provide_context,
                    "provide_context",
                )
                builder.assign_local(
                    name="additional_context",
                    value=builder.call(provide_context_name, "args", "kwargs"),
                )
            else:
                builder.assign_local(
                    name="additional_context",
                    value="{}",
                )

            scope_name = builder.global_(scope, "scope")

            context = builder.with_(
                f"container(additional_context, scope={scope_name})",
                "container",
                is_async=injected_func_type.is_async_container,
            )

        with context:
            resolved_dependencies = {}
            for name, dep in dependencies.items():
                resolved_dependencies[name] = _build_container_get(
                    dependency=dep,
                    container_name="container",
                    is_async_container=injected_func_type.is_async_container,
                    builder=builder,
                )

            call_func = builder.call(
                original_func_name,
                "*args",
                "**kwargs",
                **resolved_dependencies,
            )

            if injected_func_type.func_type is FunctionType.GENERATOR:
                if injected_func_type.is_async_func:
                    with builder.for_("message", call_func):
                        builder.yield_("message")
                else:
                    builder.yield_from(call_func)
            elif injected_func_type.func_type is FunctionType.CALLABLE:
                builder.return_(builder.await_(call_func))

    source_file_name = f"<{injected_func_name}>"
    globals_names = builder.compile(source_file_name)[injected_func_name]
    compiled_func: InjectFunc[P, T]= globals_names
    return compiled_func


def _build_container_get(
    *,
    dependency: DependencyKey,
    container_name: str,
    is_async_container: bool,
    builder: CodeBuilder,
) -> str:
    if dependency.is_const():
        return builder.global_(dependency.get_const_value())

    dep_type_hint = builder.global_(dependency.type_hint)
    dep_component = builder.global_(dependency.component)
    container_call = builder.call(
        f"{container_name}.get",
        dep_type_hint,
        dep_component,
    )
    if is_async_container:
        container_call = builder.await_(container_call)
    return container_call
