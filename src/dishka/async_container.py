from __future__ import annotations

import warnings
from asyncio import Lock
from collections.abc import Callable, MutableMapping
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, TypeVar, cast, overload

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import Has, HasContext
from dishka.entities.scope import BaseScope, Scope
from dishka.provider import Provider, activate
from .code_tools.container_compiler import (
    compile_resolvers,
    compile_scope_enters,
)
from .container_objects import Exit
from .context_proxy import ContextProxy
from .entities.validation_settings import (
    DEFAULT_VALIDATION,
    ValidationSettings,
)
from .exceptions import (
    ChildScopeNotFoundError,
    ExitError,
    NoActiveFactoryError,
    NoChildScopesError,
    NoFactoryError,
    NoNonSkippedScopesError,
)
from .graph_builder.builder import GraphBuilder
from .provider import BaseProvider, make_root_context_provider
from .registry import Registry

T = TypeVar("T")
_CACHE_MISSING = object()


class AsyncContainer:
    __slots__ = (
        "_cache",
        "_context",
        "_exits",
        "_fallback_keys",
        "_in_use",
        "_keys_default",
        "_reusable_child",
        "_reusable_wrapper",
        "child_registries",
        "close_parent",
        "lock",
        "parent_container",
        "registry",
    )

    def __init__(
            self,
            registry: Registry,
            *child_registries: Registry,
            parent_container: AsyncContainer | None = None,
            context: dict[Any, Any] | None = None,
            lock_factory: Callable[
                [], AbstractAsyncContextManager[Any],
            ] | None = None,
            close_parent: bool = False,
    ):
        self.registry = registry
        self.child_registries = child_registries
        self._context = {CONTAINER_KEY: self}
        if context:
            self._context.update(context)
        self._cache = {CONTAINER_KEY: self}
        self._fallback_keys: set[DependencyKey] = set()
        self._in_use = False
        self._keys_default: dict[Any, DependencyKey] = {}
        self._reusable_child: AsyncContainer | None = None
        self._reusable_wrapper: AsyncContextWrapper | None = None
        self.parent_container = parent_container

        self.lock: AbstractAsyncContextManager[Any] | None
        if lock_factory:
            self.lock = lock_factory()
        else:
            self.lock = None
        self._exits: list[Exit] = []
        self.close_parent = close_parent

    @property
    def scope(self) -> BaseScope:
        return self.registry.scope

    @property
    def context(self) -> MutableMapping[DependencyKey, Any]:
        warnings.warn(
            "`container.context` is deprecated",
            DeprecationWarning,
            stacklevel=2,
        )
        return ContextProxy(cache=self._cache, context=self._context)

    def __call__(
            self,
            context: dict[Any, Any] | None = None,
            lock_factory: Callable[
                [], AbstractAsyncContextManager[Any],
            ] | None = None,
            scope: BaseScope | None = None,
    ) -> AsyncContextWrapper:
        """
        Prepare container for entering the inner scope.
        :param context: Data which will available in inner scope
        :param lock_factory: Callable to create lock instance or None
        :param scope: target scope or None to enter next non-skipped scope
        :return: async context manager for inner scope
        """
        if not self.child_registries:
            raise NoChildScopesError
        if (
            context is None and
            lock_factory is None and
            scope is not None and
            self.child_registries and
            self.child_registries[0].scope is scope and
            not scope.skip
        ):
            child = self._reusable_child
            if child is None:
                child = AsyncContainer(
                    *self.child_registries,
                    parent_container=self,
                    context=None,
                    lock_factory=None,
                )
                self._reusable_child = child
                self._reusable_wrapper = AsyncContextWrapper(child)
            if not child._in_use:
                child._in_use = True
                reusable_wrapper = self._reusable_wrapper
                if reusable_wrapper is not None:
                    return reusable_wrapper
                return AsyncContextWrapper(child)
        if scope is None:
            enter_scope = self.registry.enter_default
            if enter_scope is None:
                raise NoNonSkippedScopesError
        else:
            enter_scope = self.registry.enter_scope_fns.get(scope)
            if enter_scope is None:
                raise ChildScopeNotFoundError(scope, self.registry.scope)
        child = enter_scope(self, context, lock_factory)
        return AsyncContextWrapper(child)

    @overload
    async def get(
            self,
            dependency_type: type[T],
            component: Component | None = DEFAULT_COMPONENT,
    ) -> T:
        ...

    @overload
    async def get(
            self,
            dependency_type: Any,
            component: Component | None = DEFAULT_COMPONENT,
    ) -> Any:
        ...

    async def get(
            self,
            dependency_type: Any,
            component: Component | None = DEFAULT_COMPONENT,
    ) -> Any:
        lock = self.lock
        if component == DEFAULT_COMPONENT:
            key = self._keys_default.get(dependency_type)
            if key is None:
                key = DependencyKey(dependency_type, DEFAULT_COMPONENT)
                self._keys_default[dependency_type] = key
        else:
            key = DependencyKey(dependency_type, component)
        try:
            if not lock:
                return await self._get_unlocked(key)
            async with lock:
                return await self._get_unlocked(key)
        except (NoFactoryError, NoActiveFactoryError) as e:
            e.scope = self.scope
            raise

    async def _get(self, key: DependencyKey) -> Any:
        lock = self.lock
        if not lock:
            return await self._get_unlocked(key)
        async with lock:
            return await self._get_unlocked(key)

    async def _get_unlocked(self, key: DependencyKey) -> Any:
        solved = self._cache.get(key, _CACHE_MISSING)
        if solved is not _CACHE_MISSING:
            return solved
        resolver = self.registry.resolver_async
        if resolver is not None:
            parent_get = None
            if self.parent_container is not None:
                parent_get = self.parent_container._get  # noqa: SLF001
            return await resolver(
                self._get_unlocked,
                self._exits,
                self._cache,
                self._context,
                key,
                parent_get,
                self._fallback_keys,
            )
        compiled = self.registry.get_compiled_async(key)
        if not compiled:
            if not self.parent_container:
                abstract_dependencies = (
                    self.registry.get_more_abstract_factories(key)
                )
                concrete_dependencies = (
                    self.registry.get_more_concrete_factories(key)
                )
                raise NoFactoryError(
                    key,
                    suggest_abstract_factories=abstract_dependencies,
                    suggest_concrete_factories=concrete_dependencies,
                )
            return await self.parent_container._get(key)  # noqa: SLF001
        return await compiled(
            self._get_unlocked,
            self._exits,
            self._cache,
            self._context,
        )

    async def close(  # noqa: C901
            self,
            exception: BaseException | None = None,
    ) -> None:
        errors = []
        exits = self._exits
        for exit_generator in exits[::-1]:
            try:
                if exit_generator.type is FactoryType.ASYNC_GENERATOR:
                    await exit_generator.callable.asend(exception)  # type: ignore[attr-defined]
                elif exit_generator.type is FactoryType.GENERATOR:
                    exit_generator.callable.send(exception)  # type: ignore[attr-defined]
            except StopIteration:  # noqa: PERF203
                pass
            except StopAsyncIteration:
                pass
            except Exception as err:  # noqa: BLE001
                errors.append(err)
        exits.clear()
        cache = self._cache
        if len(cache) > 1:
            cache.clear()
            cache[CONTAINER_KEY] = self
        self._in_use = False
        if self.close_parent and self.parent_container:
            try:
                await self.parent_container.close(exception)
            except Exception as err:  # noqa: BLE001
                errors.append(err)
        if errors:
            raise ExitError("Cleanup context errors", errors)  # noqa: TRY003

    async def _has(self, marker: Any) -> bool:
        resolver = self.registry.resolver_activation_async
        if resolver is not None:
            parent_has = None
            if self.parent_container is not None:
                parent_has = self.parent_container._has  # noqa: SLF001
            return cast(
                bool,
                await resolver(
                    self._get_unlocked,
                    self._exits,
                    self._cache,
                    self._context,
                    marker,
                    parent_has,
                ),
            )
        compiled = self.registry.get_compiled_activation_async(marker)
        if not compiled:
            if not self.parent_container:
                return False
            return await self.parent_container._has(marker)  # noqa: SLF001

        return bool(await compiled(
            self._get_unlocked,
            self._exits,
            self._cache,
            self._context,
        ))

    def _has_context(self, marker: Any) -> bool:
        return marker in self._context


class AsyncContextWrapper:
    def __init__(self, container: AsyncContainer):
        self.container = container

    async def __aenter__(self) -> AsyncContainer:
        return self.container

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_val: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        await self.container.close(exception=exc_val)


class HasProvider(Provider):
    @activate(Has)
    async def has(
        self,
        marker: DependencyKey,
        container: AsyncContainer,
    ) -> bool:
        key = DependencyKey(marker.type_hint.value, marker.component)
        return await container._has(key)  # noqa: SLF001

    @activate(HasContext)
    def has_context(
        self,
        marker: HasContext,
        container: AsyncContainer,
    ) -> bool:
        return container._has_context(marker.value)  # noqa: SLF001


def make_async_container(
        *providers: BaseProvider,
        scopes: type[BaseScope] = Scope,
        context: dict[Any, Any] | None = None,
        lock_factory: Callable[
            [], AbstractAsyncContextManager[Any],
        ] | None = Lock,
        skip_validation: bool = False,
        start_scope: BaseScope | None = None,
        validation_settings: ValidationSettings = DEFAULT_VALIDATION,
) -> AsyncContainer:
    context_provider = make_root_context_provider(providers, context, scopes)
    has_provider = HasProvider()
    builder = GraphBuilder(
        scopes=scopes,
        container_key=CONTAINER_KEY,
        skip_validation=skip_validation,
        validation_settings=validation_settings,
    )
    builder.add_multicomponent_providers(has_provider)
    builder.add_providers(*providers)
    builder.add_providers(context_provider)
    registries = builder.build()
    compile_scope_enters(
        registries=registries,
        container_cls=AsyncContainer,
    )
    for registry in registries:
        compile_resolvers(registry)

    container = AsyncContainer(
        *registries,
        context=context,
        lock_factory=lock_factory,
    )

    if start_scope is None:
        while container.registry.scope.skip:
            container = AsyncContainer(
                *container.child_registries,
                parent_container=container,
                context=context,
                lock_factory=lock_factory,
                close_parent=True,
            )
    else:
        while container.registry.scope is not start_scope:
            container = AsyncContainer(
                *container.child_registries,
                parent_container=container,
                context=context,
                lock_factory=lock_factory,
                close_parent=True,
            )
    return container


CONTAINER_KEY = DependencyKey(AsyncContainer, DEFAULT_COMPONENT)
