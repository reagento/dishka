from enum import Enum
from inspect import isclass
from typing import (
    Optional, Type, Callable, Union, Sequence, Any,
    get_type_hints, ClassVar, Dict,
)

from .scope import Scope


class DependencyProvider:
    def __init__(
            self,
            dependencies: Sequence,
            callable: Callable,
            result_type: Type,
            scope: Scope,
            is_context: bool = False,
            is_to_bound: bool = False,
    ):
        self.dependencies = dependencies
        self.callable = callable
        self.result_type = result_type
        self.scope = scope
        self.is_context = is_context
        self.is_to_bound = is_to_bound


def make_dependency_provider(is_context: bool, dependency: Any, scope: Optional[Scope], func: Callable):
    if isclass(func):
        hints = get_type_hints(func.__init__, include_extras=True)
        is_to_bound = False
    else:
        hints = get_type_hints(func, include_extras=True)
        is_to_bound = True
    if dependency is None:
        dependency = hints["return"]
    return DependencyProvider(
        dependencies=[
            value
            for name, value in hints.items()
            if name != "return"
        ],
        is_to_bound=is_to_bound,
        is_context=is_context,
        callable=func,
        scope=scope,
        result_type=dependency,
    )


def provide(
        func: Union[None, Callable] = None,
        *,
        scope: Scope = None,
        dependency: Any = None,
        is_context: bool = True,
):
    if func is not None:
        return make_dependency_provider(is_context, dependency, scope, func)

    def scoped(func):
        return make_dependency_provider(is_context, dependency, scope, func)

    return scoped


class Provider:
    def __init__(self):
        self.dependencies = {}
        for name, attr in vars(type(self)).items():
            if isinstance(attr, DependencyProvider):
                self.dependencies[attr.result_type] = DependencyProvider(
                    is_context=attr.is_context,
                    is_to_bound=False,
                    dependencies=attr.dependencies,
                    result_type=attr.result_type,
                    scope=attr.scope,
                    callable=attr.callable.__get__(self) if attr.is_to_bound else attr.callable
                )
