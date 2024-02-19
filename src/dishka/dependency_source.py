from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Generator,
    Iterable,
    Iterator,
)
from enum import Enum
from inspect import (
    isasyncgenfunction,
    isclass,
    iscoroutinefunction,
    isfunction,
    isgeneratorfunction,
    ismethod,
    signature,
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

from ._adaptix.type_tools.basic_utils import (
    get_all_type_hints,
    get_type_vars,
    is_bare_generic,
)
from ._adaptix.type_tools.generic_resolver import (
    GenericResolver,
    MembersStorage,
)
from .scope import BaseScope


class FactoryType(Enum):
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    FACTORY = "factory"
    ASYNC_FACTORY = "async_factory"
    VALUE = "value"

def _is_bound_method(obj):
    return ismethod(obj) and obj.__self__

def _identity(x: Any) -> Any:
    return x


class Factory:
    __slots__ = (
        "dependencies", "source", "provides", "scope", "type",
        "is_to_bound", "cache",
    )

    def __init__(
            self,
            dependencies: Sequence[Any],
            source: Any,
            provides: Type,
            scope: BaseScope | None,
            type: FactoryType,
            is_to_bound: bool,
            cache: bool,
    ):
        self.dependencies = dependencies
        self.source = source
        self.provides = provides
        self.scope = scope
        self.type = type
        self.is_to_bound = is_to_bound
        self.cache = cache

    def __get__(self, instance, owner):
        scope = self.scope or instance.scope
        if instance is None:
            return self
        if self.is_to_bound:
            source = self.source.__get__(instance, owner)
            dependencies = self.dependencies[1:]
        else:
            source = self.source
            dependencies = self.dependencies[:]
        return Factory(
            dependencies=dependencies,
            source=source,
            provides=self.provides,
            scope=scope,
            type=self.type,
            is_to_bound=False,
            cache=self.cache,
        )


def _get_init_members(tp) -> MembersStorage[str, None]:
    type_hints = get_all_type_hints(tp.__init__)
    if "__init__" in tp.__dict__:
        overriden = frozenset(type_hints)
    else:
        overriden = {}

    return MembersStorage(
        meta=None,
        members=type_hints,
        overriden=overriden,
    )


def _guess_factory_type(source):
    if isasyncgenfunction(source):
        return FactoryType.ASYNC_GENERATOR
    elif isgeneratorfunction(source):
        return FactoryType.GENERATOR
    elif iscoroutinefunction(source):
        return FactoryType.ASYNC_FACTORY
    else:
        return FactoryType.FACTORY


def _clean_result_hint(factory_type: FactoryType, possible_dependency: Any):
    if factory_type == FactoryType.ASYNC_GENERATOR:
        origin = get_origin(possible_dependency)
        if origin is AsyncIterable:
            return get_args(possible_dependency)[0]
        elif origin is AsyncIterator:
            return get_args(possible_dependency)[0]
        elif origin is AsyncGenerator:
            return get_args(possible_dependency)[0]
        else:
            raise TypeError(
                f"Unsupported return type {possible_dependency} {origin} "
                f"for async generator")
    elif factory_type == FactoryType.GENERATOR:
        origin = get_origin(possible_dependency)
        if origin is Iterable:
            return get_args(possible_dependency)[0]
        elif origin is Iterator:
            return get_args(possible_dependency)[0]
        elif origin is Generator:
            return get_args(possible_dependency)[1]
        else:
            raise TypeError(
                f"Unsupported return type {possible_dependency} {origin}"
                f" for generator")
    return possible_dependency


def make_factory(
        provides: Any,
        scope: Optional[BaseScope],
        source: Callable,
        cache: bool,
) -> Factory:
    if is_bare_generic(source):
        source = source[get_type_vars(source)]

    if isclass(source) or get_origin(source):
        # we need to fix concrete generics and normal classes as well
        # as classes can be children of concrete generics
        res = GenericResolver(_get_init_members)
        hints = dict(res.get_resolved_members(source).members)
        hints.pop("return", None)
        dependencies = list(hints.values())
        if not provides:
            provides = source
        is_to_bind = False
        factory_type = FactoryType.FACTORY
    elif isfunction(source) or isinstance(source, classmethod):
        if isinstance(source, classmethod):
            params = signature(source.__wrapped__).parameters
            factory_type = _guess_factory_type(source.__wrapped__)
        else:
            params = signature(source).parameters
            factory_type = _guess_factory_type(source)

        hints = get_type_hints(source, include_extras=True)
        self = next(iter(params.values()), None)
        if self:
            if self.name not in hints:
                # add self to dependencies, so it can be easily removed
                # if we will bind factory to provider instance
                hints = {self.name: Any, **hints}
            is_to_bind = True
        else:
            is_to_bind = False
        possible_dependency = hints.pop("return", None)
        dependencies = list(hints.values())
        if not provides:
            provides = _clean_result_hint(factory_type, possible_dependency)
    elif isinstance(source, staticmethod):
        factory_type = _guess_factory_type(source.__wrapped__)
        hints = get_type_hints(source, include_extras=True)
        possible_dependency = hints.pop("return", None)
        dependencies = list(hints.values())
        if not provides:
            provides = _clean_result_hint(factory_type, possible_dependency)
        is_to_bind = False
    elif callable(source):
        if _is_bound_method(source):
            to_check = source.__func__
        else:
            to_check = type(source).__call__
        factory = make_factory(
            provides=provides,
            source=to_check,
            cache=cache,
            scope=scope,
        )
        factory_type = factory.type
        if factory.is_to_bound:
            dependencies = factory.dependencies[1:]  # remove `self`
        provides = factory.provides
        is_to_bind = False
    else:
        raise TypeError(f"Cannot use {type(source)} as a factory")

    return Factory(
        dependencies=dependencies,
        type=factory_type,
        source=source,
        scope=scope,
        provides=provides,
        is_to_bound=is_to_bind,
        cache=cache,
    )


@overload
def provide(
        *,
        scope: BaseScope = None,
        provides: Any = None,
        cache: bool = True,
) -> Callable[[Callable], Factory]:
    ...


@overload
def provide(
        source: Callable | classmethod | staticmethod | Type | None,
        *,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
) -> Factory:
    ...


def provide(
        source: Callable | classmethod | staticmethod | Type | None = None,
        *,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
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
    :param cache: save created object to scope cache or not
    """
    if source is not None:
        return make_factory(provides, scope, source, cache)

    def scoped(func):
        return make_factory(provides, scope, func, cache)

    return scoped


class Alias:
    __slots__ = ("source", "provides", "cache")

    def __init__(self, source, provides, cache: bool):
        self.source = source
        self.provides = provides
        self.cache = cache

    def as_factory(self, scope: BaseScope) -> Factory:
        return Factory(
            scope=scope,
            source=_identity,
            provides=self.provides,
            is_to_bound=False,
            dependencies=[self.source],
            type=FactoryType.FACTORY,
            cache=self.cache,
        )

    def __get__(self, instance, owner):
        return self


def alias(
        *,
        source: Type,
        provides: Type,
        cache: bool = True,
) -> Alias:
    return Alias(
        source=source,
        provides=provides,
        cache=cache,
    )


class Decorator:
    __slots__ = ("provides", "factory")

    def __init__(self, factory: Factory):
        self.factory = factory
        self.provides = factory.provides

    def as_factory(
            self, scope: BaseScope, new_dependency: Any, cache: bool,
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
            cache=cache,
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
        return Decorator(make_factory(provides, None, source, False))

    def scoped(func):
        return Decorator(make_factory(provides, None, func, False))

    return scoped


DependencySource = Alias | Factory | Decorator
