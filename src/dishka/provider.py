from collections.abc import AsyncIterable, Iterable
from enum import Enum
from inspect import (
    isasyncgenfunction, isclass, iscoroutinefunction,
    isgeneratorfunction,
)
from typing import (
    Any, Callable, Optional, Sequence, Type, Union, get_args,
    get_origin, get_type_hints,
)

from .scope import BaseScope


class ProviderType(Enum):
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    FACTORY = "factory"
    ASYNC_FACTORY = "async_factory"
    VALUE = "value"


class DependencyProvider:
    __slots__ = (
        "dependencies", "callable", "result_type", "scope", "type",
        "is_to_bound",
    )

    def __init__(
            self,
            dependencies: Sequence,
            callable: Callable,
            result_type: Type,
            scope: Optional[BaseScope],
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

    def aliased(self, target: Type):
        return DependencyProvider(
            dependencies=self.dependencies,
            callable=self.callable,
            result_type=target,
            scope=self.scope,
            type=self.type,
            is_to_bound=self.is_to_bound,
        )


def make_dependency_provider(
        dependency: Any,
        scope: Optional[BaseScope],
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
    elif iscoroutinefunction(func):
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


class Alias:
    def __init__(self, target, result_type):
        self.target = target
        self.result_type = result_type


def alias(
        target: Type,
        dependency: Any = None,
):
    return Alias(
        target=target,
        result_type=dependency,
    )


def provide(
        func: Union[None, Callable] = None,
        *,
        scope: BaseScope = None,
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
        self.aliases = []
        for name, attr in vars(type(self)).items():
            if isinstance(attr, DependencyProvider):
                self.dependencies[attr.result_type] = getattr(self, name)
            elif isinstance(attr, Alias):
                self.aliases.append(attr)
