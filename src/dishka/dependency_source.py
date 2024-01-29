from collections.abc import AsyncIterable, Iterable
from enum import Enum
from inspect import (
    isasyncgenfunction,
    isclass,
    iscoroutinefunction,
    isgeneratorfunction,
)
from typing import (
    Any,
    Callable,
    Optional,
    Sequence,
    Type,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from .scope import BaseScope


class FactoryType(Enum):
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    FACTORY = "factory"
    ASYNC_FACTORY = "async_factory"
    VALUE = "value"


def _identity(x: Any) -> Any:
    return x


class Factory:
    __slots__ = (
        "dependencies", "source", "provides", "scope", "type",
        "is_to_bound",
    )

    def __init__(
            self,
            dependencies: Sequence[Any],
            source: Any,
            provides: Type,
            scope: Optional[BaseScope],
            type: FactoryType,
            is_to_bound: bool,
    ):
        self.dependencies = dependencies
        self.source = source
        self.provides = provides
        self.scope = scope
        self.type = type
        self.is_to_bound = is_to_bound

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.is_to_bound:
            source = self.source.__get__(instance, owner)
        else:
            source = self.source
        return Factory(
            dependencies=self.dependencies,
            source=source,
            provides=self.provides,
            scope=self.scope,
            type=self.type,
            is_to_bound=False,
        )


def make_factory(
        provides: Any,
        scope: Optional[BaseScope],
        source: Callable,
) -> Factory:
    if isclass(source):
        hints = get_type_hints(source.__init__, include_extras=True)
        hints.pop("return", None)
        possible_dependency = source
        is_to_bind = False
    else:
        hints = get_type_hints(source, include_extras=True)
        possible_dependency = hints.pop("return", None)
        is_to_bind = True

    if isclass(source):
        provider_type = FactoryType.FACTORY
    elif isasyncgenfunction(source):
        provider_type = FactoryType.ASYNC_GENERATOR
        if get_origin(possible_dependency) is AsyncIterable:
            possible_dependency = get_args(possible_dependency)[0]
        else:  # async generator
            possible_dependency = get_args(possible_dependency)[0]
    elif isgeneratorfunction(source):
        provider_type = FactoryType.GENERATOR
        if get_origin(possible_dependency) is Iterable:
            possible_dependency = get_args(possible_dependency)[0]
        else:  # generator
            possible_dependency = get_args(possible_dependency)[1]
    elif iscoroutinefunction(source):
        provider_type = FactoryType.ASYNC_FACTORY
    else:
        provider_type = FactoryType.FACTORY

    return Factory(
        dependencies=list(hints.values()),
        type=provider_type,
        source=source,
        scope=scope,
        provides=provides or possible_dependency,
        is_to_bound=is_to_bind,
    )


@overload
def provide(
        *,
        scope: BaseScope,
        provides: Any = None,
) -> Callable[[Callable], Factory]:
    ...


@overload
def provide(
        source: Callable | Type,
        *,
        scope: BaseScope,
        provides: Any = None,
) -> Factory:
    ...


def provide(
        source: Callable | Type | None = None,
        *,
        scope: BaseScope,
        provides: Any = None,
) -> Factory | Callable[[Callable], Factory]:
    """
    Mark a method or class as providing some dependency.

    If used as a method decorator then return annotation is used
    to determine what is provided. User `provides` to override that.
    Method parameters are analyzed and passed automatically.

    If used with a class a first parameter than `__init__` method parameters
    are passed automatically. If no provides is passed then it is
    supposed that class itself is a provided dependency.

    Return value must be saved as a `Provider` class attribute and
    not intended for direct usage

    :param source: Method to decorate or class.
    :param scope: Scope of the dependency to limit its lifetime
    :param provides: Dependency type which is provided by this factory
    :return: instance of Factory or a decorator returning it
    """
    if source is not None:
        return make_factory(provides, scope, source)

    def scoped(func):
        return make_factory(provides, scope, func)

    return scoped


class Alias:
    __slots__ = ("source", "provides")

    def __init__(self, source, provides):
        self.source = source
        self.provides = provides

    def as_factory(self, scope: BaseScope) -> Factory:
        return Factory(
            scope=scope,
            source=_identity,
            provides=self.provides,
            is_to_bound=False,
            dependencies=[self.source],
            type=FactoryType.FACTORY,
        )

    def __get__(self, instance, owner):
        return self


def alias(
        *,
        source: Type,
        provides: Type,
) -> Alias:
    return Alias(
        source=source,
        provides=provides,
    )


class Decorator:
    __slots__ = ("provides", "factory")

    def __init__(self, factory: Factory):
        self.factory = factory
        self.provides = factory.provides

    def as_factory(
            self, scope: BaseScope, new_dependency: Any,
    ) -> Factory:
        return Factory(
            scope=scope,
            source=self.factory.source,
            provides=self.factory.provides,
            is_to_bound=self.factory.is_to_bound,
            dependencies=[
                new_dependency if dep is self.provides else dep
                for dep in self.factory.dependencies
            ],
            type=self.factory.type,
        )

    def __get__(self, instance, owner):
        return Decorator(self.factory.__get__(instance, owner))


@overload
def decorate(
        *,
        provides: Any = None,
) -> Callable[[Callable], Decorator]:
    ...


@overload
def decorate(
        source: Callable | Type,
        *,
        provides: Any = None,
) -> Decorator:
    ...


def decorate(
        source: Callable | Type | None = None,
        provides: Any = None,
) -> Decorator | Callable[[Callable], Decorator]:
    if source is not None:
        return Decorator(make_factory(provides, None, source))

    def scoped(func):
        return Decorator(make_factory(provides, None, func))

    return scoped


DependencySource = Alias | Factory | Decorator
