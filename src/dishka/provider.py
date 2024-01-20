from collections.abc import Iterable, AsyncIterable
from enum import Enum
from inspect import isclass, iscoroutine, isasyncgenfunction, isgeneratorfunction
from typing import (
    Optional, Type, Callable, Union, Sequence, Any,
    get_type_hints, get_origin, get_args,
)

from .scope import Scope


class ProviderType(Enum):
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    FACTORY = "factory"
    ASYNC_FACTORY = "async_factory"
    VALUE = "value"


class DependencyProvider:
    __slots__ = ("dependencies", "callable", "result_type", "scope", "type", "is_to_bound")

    def __init__(
            self,
            dependencies: Sequence,
            callable: Callable,
            result_type: Type,
            scope: Scope,
            type: ProviderType,
            is_to_bound: bool
    ):
        self.dependencies = dependencies
        self.callable = callable
        self.result_type = result_type
        self.scope = scope
        self.type = type
        self.is_to_bound = is_to_bound

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.is_to_bound:
            callable = self.callable.__get__(instance, owner)
        else:
            callable = self.callable
        return DependencyProvider(
            dependencies=self.dependencies,
            callable=callable,
            result_type=self.result_type,
            scope=self.scope,
            type=self.type,
            is_to_bound=False,
        )


def make_dependency_provider(
        dependency: Any,
        scope: Optional[Scope],
        func: Callable,
):
    if isclass(func):
        hints = get_type_hints(func.__init__, include_extras=True)
        hints.pop("return", None)
        possible_dependency = func
        is_to_bind = False
    else:
        hints = get_type_hints(func, include_extras=True)
        possible_dependency = hints.pop("return", None)
        is_to_bind = True

    if isclass(func):
        provider_type = ProviderType.FACTORY
    elif isasyncgenfunction(func):
        provider_type = ProviderType.ASYNC_GENERATOR
        if get_origin(possible_dependency) is AsyncIterable:
            possible_dependency = get_args(possible_dependency)[0]
        else:  # async generator
            possible_dependency = get_args(possible_dependency)[0]
    elif isgeneratorfunction(func):
        provider_type = ProviderType.GENERATOR
        if get_origin(possible_dependency) is Iterable:
            possible_dependency = get_args(possible_dependency)[0]
        else:  # generator
            possible_dependency = get_args(possible_dependency)[1]
    elif iscoroutine(func):
        provider_type = ProviderType.ASYNC_FACTORY
    else:
        provider_type = ProviderType.FACTORY

    return DependencyProvider(
        dependencies=list(hints.values()),
        type=provider_type,
        callable=func,
        scope=scope,
        result_type=dependency or possible_dependency,
        is_to_bound=is_to_bind,
    )


def provide(
        func: Union[None, Callable] = None,
        *,
        scope: Scope = None,
        dependency: Any = None,
):
    if func is not None:
        return make_dependency_provider(dependency, scope, func)

    def scoped(func):
        return make_dependency_provider(dependency, scope, func)

    return scoped


class Provider:
    def __init__(self):
        self.dependencies = {}
        for name, attr in vars(type(self)).items():
            if isinstance(attr, DependencyProvider):
                self.dependencies[attr.result_type] = getattr(self, name)
