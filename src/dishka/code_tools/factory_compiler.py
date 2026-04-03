import asyncio
import contextlib
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from typing import Any, TypeAlias, cast

from dishka.code_tools.code_builder import CodeBuilder
from dishka.container_objects import CompiledFactory, _Pending
from dishka.dependency_source import Factory
from dishka.entities.component import Component
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import (
    AndMarker,
    BaseMarker,
    BoolMarker,
    NotMarker,
    OrMarker,
)
from dishka.exceptions import (
    NoActiveFactoryError,
    NoContextValueError,
    NoFactoryError,
    UnsupportedFactoryError,
)
from dishka.text_rendering import get_name


class FactoryBuilder(CodeBuilder):
    def __init__(
        self,
        *,
        is_async: bool,
        getter_prefix: str,
        container_key: DependencyKey,
    ) -> None:
        super().__init__(is_async=is_async)
        self.provides_name = ""
        self.cache_key = ""
        self.getter_name = ""
        self.getter_prefix = getter_prefix
        self.container_key = container_key

    def global_(self, obj: Any, preferred_name: str | None = None) -> str:
        if preferred_name is None and isinstance(obj, DependencyKey):
            type_name = get_name(obj.type_hint, include_module=False)
            preferred_name = f"key_{type_name}"
            if obj.component:
                preferred_name += f"_{obj.component}"
            if obj.depth:
                preferred_name += f"_{obj.depth}"
        return super().global_(obj, preferred_name)

    def register_provides(self, provides: DependencyKey) -> None:
        self.provides_name = self.global_(provides)
        # special object to improve dictionary lookup
        self.cache_key = self.global_(
            provides.as_compilation_key(),
            f"{self.provides_name}_cache",
        )

    def make_getter(self) -> AbstractContextManager[None]:
        raw_provides_name = self.provides_name.removeprefix("key_")
        self.getter_name = self.getter_prefix + raw_provides_name
        return self.def_(
            self.getter_name,
            ["getter", "exits", "cache", "context", "container"],
        )

    def getter(
        self,
        obj: DependencyKey,
        compiled_deps: dict[DependencyKey, CompiledFactory],
    ) -> str:
        if obj.is_const():
            return self.global_(obj.get_const_value())
        if obj.type_hint is DependencyKey:
            return self.provides_name
        if obj == self.container_key:
            return "container"
        if obj in compiled_deps:
            factory = self.global_(compiled_deps[obj])
            return self.await_(
                self.call(
                    factory,
                    "getter",
                    "exits",
                    "cache",
                    "context",
                    "container",
                ),
            )
        return self.await_(
            self.call(
                "getter",
                self.global_(obj.as_compilation_key()),
            )
        )

    def _is_pending_aware(self, factory: Factory) -> bool:
        return (
            self._is_async
            and factory.cache
            and factory.type is not FactoryType.CONTEXT
        )

    def cache(self, factory: Factory) -> None:
        if factory.cache and factory.type is not FactoryType.CONTEXT:
            self.assign_expr(f"cache[{self.cache_key}]", "solved")
            if self._is_pending_aware(factory):
                self.statement("_pending.set_result(solved)")

    def return_if_cached(self, factory: Factory) -> None:
        if factory.cache and factory.type is not FactoryType.CONTEXT:
            with self.if_(f"{self.cache_key} in cache"):
                if self._is_pending_aware(factory):
                    pending_cls = self.global_(_Pending, "_Pending")
                    self.assign_local("_cached", f"cache[{self.cache_key}]")
                    with self.if_(f"isinstance(_cached, {pending_cls})"):
                        self.return_(self.await_("_cached"))
                    self.return_("_cached")
                else:
                    self.return_(f"cache[{self.cache_key}]")

    def place_pending(self, factory: Factory) -> None:
        if self._is_pending_aware(factory):
            pending_cls = self.global_(_Pending, "_Pending")
            self.assign_local("_pending", self.call(pending_cls))
            self.assign_expr(f"cache[{self.cache_key}]", "_pending")

    def assign_solved(self, expr: str) -> None:
        self.assign_local("solved", expr)

    def when(
        self,
        marker: BaseMarker | None,
        component: Component | None,
        compiled_deps: dict[DependencyKey, CompiledFactory],
    ) -> str:
        match marker:
            case None | BoolMarker(True):
                return ""
            case AndMarker():
                return self.and_(
                    self.when(marker.left, component, compiled_deps),
                    self.when(marker.right, component, compiled_deps),
                )
            case OrMarker():
                return self.or_(
                    self.when(marker.left, component, compiled_deps),
                    self.when(marker.right, component, compiled_deps),
                )
            case NotMarker():
                return self.not_(
                    self.when(marker.marker, component, compiled_deps),
                )
            case BoolMarker(False):
                return self.global_(marker.value)
            case _:
                if component is None:
                    raise TypeError(  # noqa: TRY003
                        f"Component is None, cannot generate when condition"
                        f" with marker {marker}",
                    )
                return self.getter(
                    DependencyKey(marker, component),
                    compiled_deps,
                )

    def getter_coro(
        self,
        obj: DependencyKey,
        compiled_deps: dict[DependencyKey, CompiledFactory],
    ) -> str:
        if obj in compiled_deps:
            factory = self.global_(compiled_deps[obj])
            return self.call(
                factory,
                "getter",
                "exits",
                "cache",
                "context",
                "container",
            )
        return self.call(
            "getter",
            self.global_(obj.as_compilation_key()),
        )

    def build_getter(self) -> CompiledFactory:
        name = f"<{self.getter_name}{'_async' if self.async_str else ''}>"
        return cast(CompiledFactory, self.compile(name)[self.getter_name])

    @contextlib.contextmanager
    def handle_no_dep(self, factory: Factory) -> Iterator[None]:
        with self.try_():
            yield
        with self.except_(NoFactoryError, as_="e"):
            self.statement(
                self.call(
                    "e.add_path",
                    self.global_(factory),
                ),
            )
            self.statement("raise")
        with self.except_(NoActiveFactoryError, as_="e"):
            self.statement(
                self.call(
                    "e.add_path",
                    self.global_(factory),
                ),
            )
            self.statement("raise")


def _sync_factory_body(
    builder: FactoryBuilder,
    source_call: str,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    builder.assign_solved(source_call)


def _async_factory_body(
    builder: FactoryBuilder,
    source_call: str,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    builder.assign_solved(builder.await_(source_call))


def _generator_body(
    builder: FactoryBuilder,
    source_call: str,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    builder.assign_local("generator", source_call)
    builder.assign_solved(
        builder.call("next", "generator"),
    )
    builder.statement(
        builder.call(
            "exits.append",
            builder.tuple_literal(
                "generator",
                "None",
            ),
        ),
    )


def _async_generator_body(
    builder: FactoryBuilder,
    source_call: str,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    builder.assign_local("generator", source_call)
    builder.assign_solved(
        builder.await_(builder.call("anext", "generator")),
    )
    builder.statement(
        builder.call(
            "exits.append",
            builder.tuple_literal(
                "None",
                "generator",
            ),
        ),
    )


def _value_factory_body(
    builder: FactoryBuilder,
    source_call: str,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    builder.assign_solved(builder.global_(factory.source))


def _alias_factory_body(
    builder: FactoryBuilder,
    source_call: str,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    builder.assign_solved(
        builder.getter(factory.dependencies[0], compiled_deps),
    )


def _context_factory_body(
    builder: FactoryBuilder,
    source_call: str,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    if factory.provides == builder.container_key:
        builder.return_("container")
        return
    source = builder.global_(factory.source)
    with builder.try_():
        builder.assign_solved(f"context[{source}]")
    with builder.except_(KeyError):
        builder.raise_(
            builder.call(
                builder.global_(NoContextValueError),
                source,
            ),
        )
    with builder.except_(TypeError):
        with builder.if_("context is None"):
            builder.raise_(
                builder.call(
                    builder.global_(NoContextValueError),
                    source,
                ),
            )
        builder.raise_()


def _selector_factory_body(
    builder: FactoryBuilder,
    source_call: str,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    error_call = builder.call(
        builder.global_(NoActiveFactoryError),
        builder.global_(factory.provides),
        builder.global_(factory.when_dependencies, "when_dependencies"),
    )
    builder.raise_(error_call)


def _collection_factory_body(
    builder: FactoryBuilder,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> None:
    unconditional_factories: list[Factory] = []
    assigned = False
    for variant in factory.when_dependencies:
        condition = builder.when(
            variant.when_override,
            variant.when_component,
            compiled_deps,
        )
        if condition:
            if not assigned:
                builder.assign_solved(
                    builder.list_literal(
                        *(
                            builder.getter(f.provides, compiled_deps)
                            for f in unconditional_factories
                        ),
                    ),
                )
                assigned = True
            with builder.if_(condition):
                builder.statement(
                    builder.call(
                        "solved.append",
                        builder.getter(variant.provides, compiled_deps),
                    ),
                )
        elif assigned:
            builder.statement(
                builder.call(
                    "solved.append",
                    builder.getter(variant.provides, compiled_deps),
                ),
            )
        else:
            unconditional_factories.append(variant)
    if not assigned:
        builder.assign_solved(
            builder.list_literal(
                *(
                    builder.getter(f.provides, compiled_deps)
                    for f in unconditional_factories
                ),
            ),
        )


ASYNC_TYPES = (FactoryType.ASYNC_FACTORY, FactoryType.ASYNC_GENERATOR)
BodyGenerator: TypeAlias = Callable[
    [FactoryBuilder, str, Factory, dict[DependencyKey, CompiledFactory]],
    None,
]
BODY_GENERATORS: dict[FactoryType, BodyGenerator] = {
    FactoryType.FACTORY: _sync_factory_body,
    FactoryType.ASYNC_FACTORY: _async_factory_body,
    FactoryType.GENERATOR: _generator_body,
    FactoryType.ASYNC_GENERATOR: _async_generator_body,
    FactoryType.CONTEXT: _context_factory_body,
    FactoryType.VALUE: _value_factory_body,
    FactoryType.ALIAS: _alias_factory_body,
    FactoryType.SELECTOR: _selector_factory_body,
    # special case, value not used
    FactoryType.COLLECTION: lambda _, __, ___, ____: None,
}


def _select_when_dependency(
    builder: FactoryBuilder,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> bool:
    """return True if there is assignment in any case"""
    first = True
    for variant in factory.when_dependencies:
        condition = builder.when(
            variant.when_override,
            factory.when_component,
            compiled_deps,
        )
        solved_value = builder.getter(variant.provides, compiled_deps)
        if first and not condition:
            builder.assign_solved(solved_value)
            return True
        elif first:
            with builder.if_(condition):
                builder.assign_solved(solved_value)
        elif not condition:
            with builder.else_():
                builder.assign_solved(solved_value)
            return True
        else:
            with builder.elif_(condition):
                builder.assign_solved(solved_value)
        first = False
    return False


def _is_sync_dep(
    dep: DependencyKey,
    compiled_deps: dict[DependencyKey, CompiledFactory],
    container_key: DependencyKey,
) -> bool:
    return (
        dep.is_const()
        or dep.type_hint is DependencyKey
        or dep == container_key
    )


def _make_gathered_source_call(
    builder: FactoryBuilder,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
) -> str | None:
    async_deps: list[tuple[int, int | str, DependencyKey]] = []
    pos_exprs: dict[int, str] = {}
    kw_exprs: dict[str, str] = {}

    gather_idx = 0
    for i, dep in enumerate(factory.dependencies):
        if _is_sync_dep(dep, compiled_deps, builder.container_key):
            pos_exprs[i] = builder.getter(dep, compiled_deps)
        else:
            async_deps.append((gather_idx, i, dep))
            gather_idx += 1

    for name, dep in factory.kw_dependencies.items():
        if _is_sync_dep(dep, compiled_deps, builder.container_key):
            kw_exprs[name] = builder.getter(dep, compiled_deps)
        else:
            async_deps.append((gather_idx, name, dep))
            gather_idx += 1

    if len(async_deps) < 2:  # noqa: PLR2004
        return None

    coro_exprs = [
        builder.getter_coro(dep, compiled_deps) for _, _, dep in async_deps
    ]
    gather_func = builder.global_(asyncio.gather, "asyncio_gather")
    builder.assign_local(
        "_deps",
        builder.await_(builder.call(gather_func, *coro_exprs)),
    )

    for gather_i, key_or_idx, _ in async_deps:
        if isinstance(key_or_idx, int):
            pos_exprs[key_or_idx] = f"_deps[{gather_i}]"
        else:
            kw_exprs[key_or_idx] = f"_deps[{gather_i}]"

    ordered_pos = [pos_exprs[i] for i in range(len(factory.dependencies))]
    return builder.call(
        builder.global_(factory.source),
        *ordered_pos,
        **kw_exprs,
    )


def _make_body(
    builder: FactoryBuilder,
    factory: Factory,
    compiled_deps: dict[DependencyKey, CompiledFactory],
    *,
    can_gather: bool = False,
) -> None:
    if factory.type is FactoryType.COLLECTION:
        _collection_factory_body(builder, factory, compiled_deps)
    else:
        has_default = _select_when_dependency(
            builder,
            factory,
            compiled_deps,
        )
        if not has_default:
            source_call = None
            if can_gather and builder.async_str:
                source_call = _make_gathered_source_call(
                    builder,
                    factory,
                    compiled_deps,
                )
            if source_call is None:
                source_call = builder.call(
                    builder.global_(factory.source),
                    *(
                        builder.getter(dep, compiled_deps)
                        for dep in factory.dependencies
                    ),
                    **{
                        name: builder.getter(dep, compiled_deps)
                        for name, dep in factory.kw_dependencies.items()
                    },
                )
            body_generator = BODY_GENERATORS[factory.type]
            if factory.when_dependencies:  # conditions generated
                with builder.else_():
                    body_generator(
                        builder,
                        source_call,
                        factory,
                        compiled_deps,
                    )
            else:  # no options at all
                body_generator(
                    builder,
                    source_call,
                    factory,
                    compiled_deps,
                )


def _has_deps(factory: Factory) -> bool:
    return bool(
        factory.dependencies
        or factory.kw_dependencies
        or factory.when_dependencies,
    )


def compile_factory(
    *,
    factory: Factory,
    is_async: bool,
    compiled_deps: dict[DependencyKey, CompiledFactory],
    container_key: DependencyKey,
    can_gather: bool = False,
) -> CompiledFactory:
    if not is_async and factory.type in ASYNC_TYPES:
        raise UnsupportedFactoryError(factory)
    if factory.type not in BODY_GENERATORS:
        raise UnsupportedFactoryError(factory)

    builder = FactoryBuilder(
        is_async=is_async,
        getter_prefix="get_",
        container_key=container_key,
    )
    builder.register_provides(factory.provides)

    pending_aware = (
        is_async and factory.cache and factory.type is not FactoryType.CONTEXT
    )

    with builder.make_getter():
        builder.return_if_cached(factory)
        builder.place_pending(factory)
        if pending_aware:
            with builder.try_():
                if _has_deps(factory):
                    with builder.handle_no_dep(factory):
                        _make_body(
                            builder,
                            factory,
                            compiled_deps,
                            can_gather=can_gather,
                        )
                else:
                    _make_body(
                        builder,
                        factory,
                        compiled_deps,
                        can_gather=can_gather,
                    )
                builder.cache(factory)
                builder.return_("solved")
            with builder.except_(BaseException, as_="_exc"):
                builder.statement(
                    f"cache.pop({builder.cache_key}, None)",
                )
                builder.statement("_pending.set_exception(_exc)")
                builder.raise_()
        else:
            if _has_deps(factory):
                with builder.handle_no_dep(factory):
                    _make_body(
                        builder,
                        factory,
                        compiled_deps,
                        can_gather=can_gather,
                    )
            else:
                _make_body(
                    builder,
                    factory,
                    compiled_deps,
                    can_gather=can_gather,
                )
            builder.cache(factory)
            builder.return_("solved")

    return builder.build_getter()


def compile_activation(
    *,
    factory: Factory,
    is_async: bool,
    compiled_deps: dict[DependencyKey, CompiledFactory],
    container_key: DependencyKey,
) -> CompiledFactory:
    builder = FactoryBuilder(
        is_async=is_async,
        getter_prefix="is_active_",
        container_key=container_key,
    )
    builder.register_provides(factory.provides)
    with builder.make_getter():
        condition = builder.when(
            factory.when_active,
            factory.when_component,
            compiled_deps,
        )
        if not condition:
            builder.return_(builder.global_(True))
        else:
            with builder.handle_no_dep(factory):
                with builder.if_(condition):
                    builder.return_(builder.global_(True))
                builder.return_(builder.global_(False))

    return builder.build_getter()
