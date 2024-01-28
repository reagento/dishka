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
    List,
    Optional,
    Sequence,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints, overload,
)

from .scope import BaseScope


class ProviderType(Enum):
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    FACTORY = "factory"
    ASYNC_FACTORY = "async_factory"
    VALUE = "value"


def _identity(x: Any) -> Any:
    return x


class DependencyProvider:
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
            type: ProviderType,
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
        return DependencyProvider(
            dependencies=self.dependencies,
            source=source,
            provides=self.provides,
            scope=self.scope,
            type=self.type,
            is_to_bound=False,
        )


def make_dependency_provider(
        provides: Any,
        scope: Optional[BaseScope],
        source: Callable,
):
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
        provider_type = ProviderType.FACTORY
    elif isasyncgenfunction(source):
        provider_type = ProviderType.ASYNC_GENERATOR
        if get_origin(possible_dependency) is AsyncIterable:
            possible_dependency = get_args(possible_dependency)[0]
        else:  # async generator
            possible_dependency = get_args(possible_dependency)[0]
    elif isgeneratorfunction(source):
        provider_type = ProviderType.GENERATOR
        if get_origin(possible_dependency) is Iterable:
            possible_dependency = get_args(possible_dependency)[0]
        else:  # generator
            possible_dependency = get_args(possible_dependency)[1]
    elif iscoroutinefunction(source):
        provider_type = ProviderType.ASYNC_FACTORY
    else:
        provider_type = ProviderType.FACTORY

    return DependencyProvider(
        dependencies=list(hints.values()),
        type=provider_type,
        source=source,
        scope=scope,
        provides=provides or possible_dependency,
        is_to_bound=is_to_bind,
    )


class Alias:
    __slots__ = ("source", "provides")

    def __init__(self, source, provides):
        self.source = source
        self.provides = provides

    def as_provider(self, scope: BaseScope) -> DependencyProvider:
        return DependencyProvider(
            scope=scope,
            source=_identity,
            provides=self.provides,
            is_to_bound=False,
            dependencies=[self.source],
            type=ProviderType.FACTORY,
        )

    def __get__(self, instance, owner):
        return self


def alias(
        *,
        source: Type,
        provides: Type,
):
    return Alias(
        source=source,
        provides=provides,
    )


class Decorator:
    __slots__ = ("provides", "provider")

    def __init__(self, provider: DependencyProvider):
        self.provider = provider
        self.provides = provider.provides

    def as_provider(
            self, scope: BaseScope, new_dependency: Any,
    ) -> DependencyProvider:
        return DependencyProvider(
            scope=scope,
            source=self.provider.source,
            provides=self.provider.provides,
            is_to_bound=self.provider.is_to_bound,
            dependencies=[
                new_dependency if dep is self.provides else dep
                for dep in self.provider.dependencies
            ],
            type=self.provider.type,
        )

    def __get__(self, instance, owner):
        return Decorator(self.provider.__get__(instance, owner))


def decorate(
        source: Union[None, Callable, Type] = None,
        provides: Any = None,
):
    if source is not None:
        return Decorator(make_dependency_provider(provides, None, source))

    def scoped(func):
        return Decorator(make_dependency_provider(provides, None, func))

    return scoped


@overload
def provide(
        *,
        scope: BaseScope,
        provides: Any = None,
) -> Callable[[Callable], DependencyProvider]:
    ...


@overload
def provide(
        source: Union[Callable, Type],
        *,
        scope: BaseScope,
        provides: Any = None,
) -> DependencyProvider:
    ...


def provide(
        source: Union[None, Callable, Type] = None,
        *,
        scope: BaseScope,
        provides: Any = None,
):
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
    :return: instance of DependencyProvider or a decorator returning it
    """
    if source is not None:
        return make_dependency_provider(provides, scope, source)

    def scoped(func):
        return make_dependency_provider(provides, scope, func)

    return scoped


DependencyProviderVariant = Alias | DependencyProvider | Decorator


class Provider:
    """
    A collection of factories providing dependencies.

    Inherit this class and add attributes using
    `provide`, `alias` or `decorate`.

    You can use `__init__`, regular methods and attributes as usual,
    they won't be analyzed when creating a container

    The only intended usage of providers is to pass them when
    creating a container
    """

    def __init__(self):
        self.dependency_providers: List[DependencyProviderVariant] = []
        for name, attr in vars(type(self)).items():
            if isinstance(attr, DependencyProviderVariant):
                self.dependency_providers.append(getattr(self, name))
