from asyncio import iscoroutinefunction
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Generator,
    Iterable,
    Iterator,
    Sequence,
)
from inspect import (
    Parameter,
    isasyncgenfunction,
    isbuiltin,
    isclass,
    isfunction,
    isgeneratorfunction,
    ismethod,
    signature,
    unwrap,
)
from typing import (
    Annotated,
    Any,
    Protocol,
    TypeAlias,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from dishka._adaptix.type_tools.basic_utils import (  # type: ignore[attr-defined]
    get_type_vars,
    is_bare_generic,
    strip_alias,
)
from dishka._adaptix.type_tools.fundamentals import (
    get_all_type_hints,
)
from dishka._adaptix.type_tools.generic_resolver import (
    GenericResolver,
    MembersStorage,
)
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import (
    dependency_key_to_hint,
    hint_to_dependency_key,
    hints_to_dependency_keys,
)
from dishka.entities.provides_marker import ProvideMultiple
from dishka.entities.scope import BaseScope
from dishka.text_rendering import get_name
from .composite import CompositeDependencySource, ensure_composite
from .factory import Factory
from .unpack_provides import unpack_factory

_empty = signature(lambda a: 0).parameters["a"].annotation
_protocol_init = type("_stub_proto", (Protocol,), {}).__init__  # type: ignore[misc, arg-type]
ProvideSource: TypeAlias = (
    Callable[..., Any]
    | classmethod  # type: ignore[type-arg]
    | staticmethod  # type: ignore[type-arg]
    | type
)


def _is_bound_method(obj: Any) -> bool:
    return ismethod(obj) and bool(obj.__self__)


def _get_init_members(tp: type) -> MembersStorage[str, None]:
    type_hints = get_all_type_hints(tp.__init__)  # type: ignore[misc, no-untyped-call]
    if "__init__" in tp.__dict__:
        overridden = frozenset(type_hints)
    else:
        overridden = frozenset()

    return MembersStorage(
        meta=None,
        members=type_hints,
        overriden=overridden,
    )


def _guess_factory_type(source: Any) -> FactoryType:
    if isasyncgenfunction(source):
        return FactoryType.ASYNC_GENERATOR
    elif isgeneratorfunction(source):
        return FactoryType.GENERATOR
    elif iscoroutinefunction(source):
        return FactoryType.ASYNC_FACTORY
    else:
        return FactoryType.FACTORY


def _type_repr(hint: Any) -> str:
    if hint is type(None):
        return "None"
    return get_name(hint, include_module=True)


def _async_generator_result(hint: Any) -> Any:
    if get_origin(hint) is ProvideMultiple:
        return ProvideMultiple[tuple(  # type: ignore[misc]
            _async_generator_result(x) for x in get_args(hint)
        )]
    origin = get_origin(hint)
    if origin is AsyncIterable:
        return get_args(hint)[0]
    elif origin is AsyncIterator:
        return get_args(hint)[0]
    elif origin is AsyncGenerator:
        return get_args(hint)[0]
    # errors
    name = _type_repr(hint)
    if origin is Iterable:
        args = ", ".join(_type_repr(a) for a in get_args(hint))
        guess = "AsyncIterable"
    elif origin is Iterator:
        args = ", ".join(_type_repr(a) for a in get_args(hint))
        guess = "AsyncIterator"
    elif origin is Generator:
        args = ", ".join(_type_repr(a) for a in get_args(hint)[:2])
        guess = "AsyncGenerator"
    else:
        args = name
        guess = "AsyncIterable"

    raise TypeError(
        f"Unsupported return type `{name}` for async generator. "
        f"Did you mean {guess}[{args}]?",
    )


def _generator_result(hint: Any) -> Any:
    if get_origin(hint) is ProvideMultiple:
        return ProvideMultiple[tuple(  # type: ignore[misc]
            _generator_result(x) for x in get_args(hint)
        )]
    origin = get_origin(hint)
    if origin is Iterable:
        return get_args(hint)[0]
    elif origin is Iterator:
        return get_args(hint)[0]
    elif origin is Generator:
        return get_args(hint)[1]
    # errors
    name = _type_repr(hint)
    if origin is AsyncIterable:
        args = ", ".join(_type_repr(a) for a in get_args(hint))
        guess = "Iterable"
    elif origin is AsyncIterator:
        args = ", ".join(_type_repr(a) for a in get_args(hint))
        guess = "Iterator"
    elif origin is AsyncGenerator:
        args = ", ".join(_type_repr(a) for a in get_args(hint)) + ", None"
        guess = "Generator"
    else:
        args = name
        guess = "Iterable"

    raise TypeError(
        f"Unsupported return type `{name}` for generator. "
        f"Did you mean {guess}[{args}]?",
    )


def _clean_result_hint(
    factory_type: FactoryType,
    possible_dependency: Any,
) -> Any:
    if factory_type == FactoryType.ASYNC_GENERATOR:
        return _async_generator_result(possible_dependency)
    elif factory_type == FactoryType.GENERATOR:
        return _generator_result(possible_dependency)
    return possible_dependency


def _params_without_hints(func: Any, *, skip_self: bool) -> Sequence[str]:
    if func is object.__init__:
        return []
    if func is _protocol_init:
        return []
    params = signature(func).parameters
    return [
        p.name
        for i, p in enumerate(params.values())
        if p.annotation is _empty
        if i > 0 or not skip_self
    ]


def _make_factory_by_class(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: type,
        cache: bool,
        override: bool,
) -> Factory:
    if not provides:
        provides = source

    if get_origin(source) is Annotated:
        source = get_args(source)[0]
    init = strip_alias(source).__init__
    if missing_hints := _params_without_hints(init, skip_self=True):
        name = get_name(source, include_module=True) + ".__init__"
        missing = ", ".join(missing_hints)
        raise ValueError(
            f"Failed to analyze `{name}`. \n"
            f"Some parameters do not have type hints: {missing}\n",
        )
    # we need to fix concrete generics and normal classes as well
    # as classes can be children of concrete generics
    res = GenericResolver(_get_init_members)
    try:
        hints = dict(res.get_resolved_members(source).members)
    except NameError as e:
        name = get_name(source, include_module=True) + ".__init__"
        raise NameError(
            f"Failed to analyze `{name}`. \n"
            f"Type '{e.name}' is not defined\n\n"
            f"If your are using `if TYPE_CHECKING` to import '{e.name}' "
            f"then try removing it. \n"
            f"Or, create a separate factory with all types imported.",
            name=e.name,
        ) from e

    hints.pop("return", _empty)
    params = signature(init).parameters
    kw_dependency_keys = {
        name: hint_to_dependency_key(hints.pop(name))
        for name, param in params.items()
        if param.kind is Parameter.KEYWORD_ONLY
    }
    dependencies = list(hints.values())

    return Factory(
        dependencies=hints_to_dependency_keys(dependencies),
        kw_dependencies=kw_dependency_keys,
        type_=FactoryType.FACTORY,
        source=source,
        scope=scope,
        provides=hint_to_dependency_key(provides),
        is_to_bind=False,
        cache=cache,
        override=override,
    )


def _make_factory_by_function(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: Callable[..., Any] | classmethod, # type: ignore[type-arg]
        cache: bool,
        is_in_class: bool,
        override: bool,
) -> Factory:
    # typing.cast is applied as unwrap takes a Callable object
    raw_source = unwrap(cast(Callable[..., Any], source))
    missing_hints = _params_without_hints(raw_source, skip_self=is_in_class)
    if missing_hints:
        name = get_name(source, include_module=True)
        missing = ", ".join(missing_hints)
        raise ValueError(
            f"Failed to analyze `{name}`. \n"
            f"Some parameters do not have type hints: {missing}\n",
        )

    params = signature(raw_source).parameters
    factory_type = _guess_factory_type(raw_source)

    try:
        hints = get_type_hints(source, include_extras=True)
    except NameError as e:
        name = get_name(source, include_module=True)
        raise NameError(
            f"Failed to analyze `{name}`. \n"
            f"Type '{e.name}' is not defined. \n\n"
            f"If your are using `if TYPE_CHECKING` to import '{e.name}' "
            f"then try removing it. \n"
            f"Or, create a separate factory with all types imported.",
            name=e.name,
        ) from e
    if is_in_class:
        self = next(iter(params.values()), None)
        if self and self.name not in hints:
            # add self to dependencies, so it can be easily removed
            # if we will bind factory to provider instance
            hints = {self.name: Any, **hints}
    possible_dependency = hints.pop("return", _empty)

    kw_dependency_keys = {
        name: hint_to_dependency_key(hints.pop(name))
        for name, param in params.items()
        if param.kind is Parameter.KEYWORD_ONLY
    }
    dependencies = list(hints.values())

    if not provides:
        if possible_dependency is _empty:
            name = get_name(source, include_module=True)
            raise ValueError(f"Failed to analyze `{name}`. \n"
                             f"Missing return type hint.")
        try:
            provides = _clean_result_hint(factory_type, possible_dependency)
        except TypeError as e:
            name = get_name(source, include_module=True)
            raise TypeError(f"Failed to analyze `{name}`. \n" + str(e)) from e
    return Factory(
        dependencies=hints_to_dependency_keys(dependencies),
        kw_dependencies=kw_dependency_keys,
        type_=factory_type,
        source=source,
        scope=scope,
        provides=hint_to_dependency_key(provides),
        is_to_bind=is_in_class,
        cache=cache,
        override=override,
    )


def _make_factory_by_static_method(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: staticmethod,  # type: ignore[type-arg]
        cache: bool,
        override: bool,
) -> Factory:
    if missing_hints := _params_without_hints(source, skip_self=False):
        name = get_name(source, include_module=True)
        missing = ", ".join(missing_hints)
        raise ValueError(
            f"Failed to analyze `{name}`. \n"
            f"Some parameters do not have type hints: {missing}\n",
        )
    factory_type = _guess_factory_type(source.__wrapped__)
    try:
        hints = get_type_hints(source, include_extras=True)
    except NameError as e:
        name = get_name(source, include_module=True)
        raise NameError(
            f"Failed to analyze `{name}`. \n"
            f"Type '{e.name}' is not defined. \n\n"
            f"If your are using `if TYPE_CHECKING` to import '{e.name}' "
            f"then try removing it. \n"
            f"Or, create a separate factory with all types imported.",
            name=e.name,
        ) from e

    possible_dependency = hints.pop("return", _empty)

    params = signature(source).parameters
    kw_dependency_keys = {
        name: hint_to_dependency_key(hints.pop(name))
        for name, param in params.items()
        if param.kind is Parameter.KEYWORD_ONLY
    }
    dependencies = list(hints.values())

    if not provides:
        if possible_dependency is _empty:
            name = get_name(source, include_module=True)
            raise ValueError(f"Failed to analyze `{name}`. \n"
                             f"Missing return type hint.")
        try:
            provides = _clean_result_hint(factory_type, possible_dependency)
        except TypeError as e:
            name = get_name(source, include_module=True)
            raise TypeError(f"Failed to analyze `{name}`. \n" + str(e)) from e
    return Factory(
        dependencies=hints_to_dependency_keys(dependencies),
        kw_dependencies=kw_dependency_keys,
        type_=factory_type,
        source=source,
        scope=scope,
        provides=hint_to_dependency_key(provides),
        is_to_bind=False,
        cache=cache,
        override=override,
    )


def _make_factory_by_other_callable(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: Callable[..., Any],
        cache: bool,
        override: bool,
) -> Factory:
    if _is_bound_method(source):
        to_check = source.__func__  # type: ignore[attr-defined]
    else:
        to_check = type(source).__call__
    factory = make_factory(
        provides=provides,
        source=to_check,
        cache=cache,
        scope=scope,
        is_in_class=True,
        override=override,
    )
    if factory.is_to_bind:
        dependencies = factory.dependencies[1:]  # remove `self`
    else:
        dependencies = factory.dependencies
    return Factory(
        dependencies=dependencies,
        kw_dependencies=factory.kw_dependencies,
        type_=factory.type,
        source=source,
        scope=scope,
        provides=factory.provides,
        is_to_bind=False,
        cache=cache,
        override=override,
    )


def make_factory(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: ProvideSource,
        cache: bool,
        is_in_class: bool,
        override: bool,
) -> Factory:
    if get_origin(source) is ProvideMultiple:
        if provides is None:
            provides = source
        source = get_args(source)[0]

    if is_bare_generic(source):
        source = source[get_type_vars(source)]  # type: ignore[index]

    if isclass(source) or get_origin(source):
        return _make_factory_by_class(
            provides=provides,
            scope=scope,
            source=cast(type, source),
            cache=cache,
            override=override,
        )
    elif isfunction(source) or isinstance(source, classmethod):
        return _make_factory_by_function(
            provides=provides,
            scope=scope,
            source=source,
            cache=cache,
            is_in_class=is_in_class,
            override=override,
        )
    elif isbuiltin(source):
        return _make_factory_by_function(
            provides=provides,
            scope=scope,
            source=source,
            cache=cache,
            is_in_class=False,
            override=override,
        )
    elif isinstance(source, staticmethod):
        return _make_factory_by_static_method(
            provides=provides,
            scope=scope,
            source=source,
            cache=cache,
            override=override,
        )
    elif callable(source):
        return _make_factory_by_other_callable(
            provides=provides,
            scope=scope,
            source=source,
            cache=cache,
            override=override,
        )
    else:
        raise TypeError(f"Cannot use {type(source)} as a factory")


def _provide(
        *,
        source: ProvideSource | None = None,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
        is_in_class: bool = True,
        recursive: bool = False,
        override: bool = False,
) -> CompositeDependencySource:
    composite = ensure_composite(source)
    factory = make_factory(
        provides=provides, scope=scope,
        source=composite.origin, cache=cache,
        is_in_class=is_in_class,
        override=override,
    )
    composite.dependency_sources.extend(unpack_factory(factory))
    if not recursive:
        return composite

    for src in composite.dependency_sources:
        if not isinstance(src, Factory):
            # we expect Factory and Alias here
            continue
        for dependency in src.dependencies:
            additional = _provide(
                provides=dependency_key_to_hint(dependency),
                scope=scope,
                source=dependency.type_hint,
                cache=cache,
                is_in_class=is_in_class,
                override=override,
            )
            composite.dependency_sources.extend(additional.dependency_sources)
    return composite


def provide_on_instance(
        *,
        source: ProvideSource | None = None,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
        recursive: bool = False,
        override: bool = False,
) -> CompositeDependencySource:
    return _provide(
        provides=provides, scope=scope, source=source, cache=cache,
        is_in_class=False,
        recursive=recursive, override=override,
    )


@overload
def provide(
        *,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
        recursive: bool = False,
        override: bool = False,
) -> Callable[[Callable[..., Any]], CompositeDependencySource]:
    ...


@overload
def provide(
        source: ProvideSource | None,
        *,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
        recursive: bool = False,
        override: bool = False,
) -> CompositeDependencySource:
    ...


def provide(
        source: ProvideSource | None = None,
        *,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
        recursive: bool = False,
        override: bool = False,
) -> CompositeDependencySource | Callable[
    [Callable[..., Any]], CompositeDependencySource,
]:
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
    :param cache: save created object to scope cache or not
    :param recursive: register dependencies as factories as well
    :param override: dependency override
    :return: instance of Factory or a decorator returning it
    """
    if source is not None:
        return _provide(
            provides=provides, scope=scope, source=source, cache=cache,
            is_in_class=True, recursive=recursive, override=override,
        )

    def scoped(func: Callable[..., Any]) -> CompositeDependencySource:
        return _provide(
            provides=provides, scope=scope, source=func, cache=cache,
            is_in_class=True, recursive=recursive, override=override,
        )

    return scoped


def _provide_all(
        *,
        provides: Sequence[Any],
        scope: BaseScope | None,
        cache: bool,
        is_in_class: bool,
        recursive: bool,
        override: bool = False,
) -> CompositeDependencySource:
    composite = CompositeDependencySource(None)
    for single_provides in provides:
        source = _provide(
            source=single_provides,
            provides=single_provides,
            scope=scope,
            cache=cache,
            is_in_class=is_in_class,
            recursive=recursive,
            override=override,
        )
        composite.dependency_sources.extend(source.dependency_sources)
    return composite


def provide_all(
        *provides: Any,
        scope: BaseScope | None = None,
        cache: bool = True,
        recursive: bool = False,
        override: bool = False,
) -> CompositeDependencySource:
    return _provide_all(
        provides=provides, scope=scope,
        cache=cache, is_in_class=True,
        recursive=recursive, override=override,
    )


def provide_all_on_instance(
        *provides: Any,
        scope: BaseScope | None = None,
        cache: bool = True,
        recursive: bool = False,
        override: bool = False,
) -> CompositeDependencySource:
    return _provide_all(
        provides=provides, scope=scope,
        cache=cache, is_in_class=False,
        recursive=recursive, override=override,
    )
