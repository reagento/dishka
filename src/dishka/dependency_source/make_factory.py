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
    isasyncgenfunction,
    isbuiltin,
    isclass,
    iscoroutinefunction,
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
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from dishka._adaptix.type_tools.basic_utils import (
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
from dishka.entities.key import (
    hint_to_dependency_key,
    hints_to_dependency_keys,
)
from dishka.entities.scope import BaseScope
from .composite import CompositeDependencySource, ensure_composite
from .factory import Factory, FactoryType
from .unpack_provides import unpack_factory

_empty = signature(lambda a: 0).parameters["a"].annotation
_protocol_init = type("_stub_proto", (Protocol,), {}).__init__


def _is_bound_method(obj):
    return ismethod(obj) and obj.__self__


def _get_init_members(tp) -> MembersStorage[str, None]:
    type_hints = get_all_type_hints(tp.__init__)
    if "__init__" in tp.__dict__:
        overridden = frozenset(type_hints)
    else:
        overridden = {}

    return MembersStorage(
        meta=None,
        members=type_hints,
        overriden=overridden,
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


def _type_repr(hint: Any) -> str:
    if hint is type(None):
        return "None"
    module = getattr(hint, "__module__", "")
    if module == "builtins":
        module = ""
    elif module:
        module += "."
    try:
        return f"{module}{hint.__qualname__}"
    except AttributeError:
        return str(hint)


def _async_generator_result(hint: Any):
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


def _generator_result(hint: Any):
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


def _clean_result_hint(factory_type: FactoryType, possible_dependency: Any):
    if factory_type == FactoryType.ASYNC_GENERATOR:
        return _async_generator_result(possible_dependency)
    elif factory_type == FactoryType.GENERATOR:
        return _generator_result(possible_dependency)
    return possible_dependency


def _params_without_hints(func, *, skip_self: bool) -> Sequence[str]:
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
        source: Callable,
        cache: bool,
) -> Factory:
    if not provides:
        provides = source

    if get_origin(source) is Annotated:
        source = get_args(source)[0]
    init = strip_alias(source).__init__
    if missing_hints := _params_without_hints(init, skip_self=True):
        name = f"{source.__module__}.{source.__qualname__}.__init__"
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
        name = f"{source.__module__}.{source.__qualname__}.__init__"
        raise NameError(
            f"Failed to analyze `{name}`. \n"
            f"Type '{e.name}' is not defined\n\n"
            f"If your are using `if TYPE_CHECKING` to import '{e.name}' "
            f"then try removing it. \n"
            f"Or, create a separate factory with all types imported.",
            name=e.name,
        ) from e

    hints.pop("return", _empty)
    dependencies = list(hints.values())

    return Factory(
        dependencies=hints_to_dependency_keys(dependencies),
        type_=FactoryType.FACTORY,
        source=source,
        scope=scope,
        provides=hint_to_dependency_key(provides),
        is_to_bind=False,
        cache=cache,
    )


def _make_factory_by_function(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: Callable | classmethod,
        cache: bool,
        is_in_class: bool,
) -> Factory:
    raw_source = unwrap(source)
    missing_hints = _params_without_hints(raw_source, skip_self=is_in_class)
    if missing_hints:
        name = getattr(source, "__qualname__", "") or str(source)
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
        name = getattr(source, "__qualname__", "") or str(source)
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
    dependencies = list(hints.values())
    if not provides:
        if possible_dependency is _empty:
            name = getattr(source, "__qualname__", "") or str(source)
            raise ValueError(f"Failed to analyze `{name}`. \n"
                             f"Missing return type hint.")
        try:
            provides = _clean_result_hint(factory_type, possible_dependency)
        except TypeError as e:
            name = getattr(source, "__qualname__", "") or str(source)
            raise TypeError(f"Failed to analyze `{name}`. \n" + str(e)) from e
    return Factory(
        dependencies=hints_to_dependency_keys(dependencies),
        type_=factory_type,
        source=source,
        scope=scope,
        provides=hint_to_dependency_key(provides),
        is_to_bind=is_in_class,
        cache=cache,
    )


def _make_factory_by_static_method(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: staticmethod,
        cache: bool,
) -> Factory:
    if missing_hints := _params_without_hints(source, skip_self=False):
        name = getattr(source, "__qualname__", "") or str(source)
        missing = ", ".join(missing_hints)
        raise ValueError(
            f"Failed to analyze `{name}`. \n"
            f"Some parameters do not have type hints: {missing}\n",
        )
    factory_type = _guess_factory_type(source.__wrapped__)
    try:
        hints = get_type_hints(source, include_extras=True)
    except NameError as e:
        name = getattr(source, "__qualname__", "") or str(source)
        raise NameError(
            f"Failed to analyze `{name}`. \n"
            f"Type '{e.name}' is not defined. \n\n"
            f"If your are using `if TYPE_CHECKING` to import '{e.name}' "
            f"then try removing it. \n"
            f"Or, create a separate factory with all types imported.",
            name=e.name,
        ) from e
    possible_dependency = hints.pop("return", _empty)
    dependencies = list(hints.values())
    if not provides:
        if possible_dependency is _empty:
            name = getattr(source, "__qualname__", "") or str(source)
            raise ValueError(f"Failed to analyze `{name}`. \n"
                             f"Missing return type hint.")
        try:
            provides = _clean_result_hint(factory_type, possible_dependency)
        except TypeError as e:
            name = getattr(source, "__qualname__", "") or str(source)
            raise TypeError(f"Failed to analyze `{name}`. \n" + str(e)) from e
    return Factory(
        dependencies=hints_to_dependency_keys(dependencies),
        type_=factory_type,
        source=source,
        scope=scope,
        provides=hint_to_dependency_key(provides),
        is_to_bind=False,
        cache=cache,
    )


def _make_factory_by_other_callable(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: Callable,
        cache: bool,
) -> Factory:
    if _is_bound_method(source):
        to_check = source.__func__
    else:
        to_check = type(source).__call__
    factory = make_factory(
        provides=provides,
        source=to_check,
        cache=cache,
        scope=scope,
        is_in_class=True,
    )
    if factory.is_to_bind:
        dependencies = factory.dependencies[1:]  # remove `self`
    else:
        dependencies = factory.dependencies
    return Factory(
        dependencies=dependencies,
        type_=factory.type,
        source=source,
        scope=scope,
        provides=factory.provides,
        is_to_bind=False,
        cache=cache,
    )


def make_factory(
        *,
        provides: Any,
        scope: BaseScope | None,
        source: Callable,
        cache: bool,
        is_in_class: bool,
) -> Factory:
    if is_bare_generic(source):
        source = source[get_type_vars(source)]

    if isclass(source) or get_origin(source):
        return _make_factory_by_class(
            provides=provides, scope=scope, source=source, cache=cache,
        )
    elif isfunction(source) or isinstance(source, classmethod):
        return _make_factory_by_function(
            provides=provides, scope=scope, source=source, cache=cache,
            is_in_class=is_in_class,
        )
    elif isbuiltin(source):
        return _make_factory_by_function(
            provides=provides, scope=scope, source=source, cache=cache,
            is_in_class=False,
        )
    elif isinstance(source, staticmethod):
        return _make_factory_by_static_method(
            provides=provides, scope=scope, source=source, cache=cache,
        )
    elif callable(source):
        return _make_factory_by_other_callable(
            provides=provides, scope=scope, source=source, cache=cache,
        )
    else:
        raise TypeError(f"Cannot use {type(source)} as a factory")


def _provide(
        *,
        source: Callable | classmethod | staticmethod | type | None = None,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
        is_in_class: bool = True,
) -> CompositeDependencySource:
    composite = ensure_composite(source)
    factory = make_factory(
        provides=provides, scope=scope,
        source=composite.origin, cache=cache,
        is_in_class=is_in_class,
    )
    composite.dependency_sources.extend(unpack_factory(factory))
    return composite


def provide_on_instance(
        *,
        source: Callable | classmethod | staticmethod | type | None = None,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
) -> CompositeDependencySource:
    return _provide(
        provides=provides, scope=scope, source=source, cache=cache,
        is_in_class=False,
    )


@overload
def provide(
        *,
        scope: BaseScope = None,
        provides: Any = None,
        cache: bool = True,
) -> Callable[[Callable], CompositeDependencySource]:
    ...


@overload
def provide(
        source: Callable | classmethod | staticmethod | type | None,
        *,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
) -> CompositeDependencySource:
    ...


def provide(
        source: Callable | classmethod | staticmethod | type | None = None,
        *,
        scope: BaseScope | None = None,
        provides: Any = None,
        cache: bool = True,
) -> Any:
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
        return _provide(
            provides=provides, scope=scope, source=source, cache=cache,
            is_in_class=True,
        )

    def scoped(func):
        return _provide(
            provides=provides, scope=scope, source=func, cache=cache,
            is_in_class=True,
        )

    return scoped


def _provide_all(
        *,
        provides: Sequence[Any],
        scope: BaseScope | None,
        cache: bool,
        is_in_class: bool,
) -> CompositeDependencySource:
    composite = CompositeDependencySource(None)
    for single_provides in provides:
        factory = make_factory(
            provides=single_provides, scope=scope,
            source=single_provides, cache=cache,
            is_in_class=is_in_class,
        )
        composite.dependency_sources.extend(unpack_factory(factory))
    return composite


def provide_all(
        *provides: Any,
        scope: BaseScope | None = None,
        cache: bool = True,
) -> CompositeDependencySource:
    return _provide_all(
        provides=provides, scope=scope,
        cache=cache, is_in_class=True,
    )


def provide_all_on_instance(
        *provides: Any,
        scope: BaseScope | None = None,
        cache: bool = True,
) -> CompositeDependencySource:
    return _provide_all(
        provides=provides, scope=scope,
        cache=cache, is_in_class=False,
    )
