import warnings
from asyncio import Lock
from collections.abc import Awaitable, Callable, MutableMapping
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, TypeVar, overload

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.key import DependencyKey
from dishka.entities.marker import Has, HasContext
from dishka.entities.scope import BaseScope, Scope
from dishka.provider import Provider, activate
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

ExitCallable = Callable[
    [type | None, BaseException | None, TracebackType | None],
    Awaitable[None],
]


class AsyncContainer:
    __slots__ = (
        "_cache",
        "_context",
        "_exits",
        "child_registries",
        "lock",
        "parent_closer",
        "parent_container",
        "parent_getter",
        "registry",
    )

    def __init__(
            self,
            registry: Registry,
            *child_registries: Registry,
            parent_container: "AsyncContainer | None" = None,
            context: dict[Any, Any] | None = None,
            lock_factory: Callable[
                [], AbstractAsyncContextManager[Any],
            ] | None = None,
            parent_closer: ExitCallable | None = None,
            parent_getter:  Callable[[DependencyKey], Any] | None  = None,
    ):
        self.registry = registry
        self.child_registries = child_registries
        if context is None:
            self._context = {AsyncContainer: self}
        else:
            self._context = {AsyncContainer: self, **context}
        self._cache: dict[DependencyKey, object] = {}
        self.parent_container = parent_container

        self.lock: AbstractAsyncContextManager[Any] | None
        if lock_factory is None:
            self.lock = None
        else:
            self.lock = lock_factory()
        self._exits: list[Exit] = []
        self.parent_closer = parent_closer
        self.parent_getter = parent_getter

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
    ) -> "AsyncContainer":
        """
        Prepare container for entering the inner scope.
        :param context: Data which will available in inner scope
        :param lock_factory: Callable to create lock instance or None
        :param scope: target scope or None to enter next non-skipped scope
        :return: async context manager for inner scope
        """
        if not self.child_registries:
            raise NoChildScopesError

        child = AsyncContainer(
            *self.child_registries,
            parent_container=self,
            context=context,
            lock_factory=lock_factory,
            parent_getter=self._get,
        )
        if scope is None:
            while child.registry.scope.skip:
                if not child.child_registries:
                    raise NoNonSkippedScopesError
                child = AsyncContainer(
                    *child.child_registries,
                    parent_container=child,
                    context=context,
                    lock_factory=lock_factory,
                    parent_closer=child.__aexit__,
                    parent_getter=child._get,
                )
        else:
            while child.registry.scope is not scope:
                if not child.child_registries:
                    raise ChildScopeNotFoundError(scope, self.registry.scope)
                child = AsyncContainer(
                    *child.child_registries,
                    parent_container=child,
                    context=context,
                    lock_factory=lock_factory,
                    parent_closer=child.__aexit__,
                    parent_getter=child._get,
                )
        return child

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
        key = DependencyKey(dependency_type, component)
        try:
            if lock is None:
                return await self._get_unlocked(key)
            async with lock:
                return await self._get_unlocked(key)
        except (NoFactoryError, NoActiveFactoryError) as e:
            e.scope = self.scope
            raise

    @overload
    def get_sync(
            self,
            dependency_type: type[T],
            component: Component | None = DEFAULT_COMPONENT,
    ) -> T:
        ...

    @overload
    def get_sync(
            self,
            dependency_type: Any,
            component: Component | None = DEFAULT_COMPONENT,
    ) -> Any:
        ...

    def get_sync(
        self,
        dependency_type: Any,
        component: Component | None = DEFAULT_COMPONENT,
    ) -> Any:
        key = DependencyKey(dependency_type, component)
        try:
            return self._get_sync(key)
        except (NoFactoryError, NoActiveFactoryError) as e:
            e.scope = self.scope
            raise

    def _get_sync(self, key: DependencyKey) -> Any:
        compiled = self.registry.get_compiled(key)
        if compiled is None:
            if self.parent_container is None:
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
            try:
                return self.parent_container._get_sync(key)  # noqa: SLF001
            except NoFactoryError as ex:
                abstract_dependencies = (
                    self.registry.get_more_abstract_factories(key)
                )
                concrete_dependencies = (
                    self.registry.get_more_concrete_factories(key)
                )
                ex.suggest_abstract_factories.extend(abstract_dependencies)
                ex.suggest_concrete_factories.extend(concrete_dependencies)
                raise

        return compiled(
            (
                self.parent_container._get_sync  # noqa: SLF001
                if self.parent_container
                else None
            ),
            self._exits,
            self._cache,
            self._context,
        )

    async def _get(self, key: DependencyKey) -> Any:
        lock = self.lock
        if lock is None:
            return await self._get_unlocked(key)
        async with lock:
            return await self._get_unlocked(key)

    async def _get_unlocked(self, key: DependencyKey) -> Any:
        compiled = self.registry.get_compiled_async(key)
        if compiled is None:
            if self.parent_getter is None:
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
            try:
                return await self.parent_getter(key)
            except NoFactoryError as ex:
                abstract_dependencies = (
                    self.registry.get_more_abstract_factories(key)
                )
                concrete_dependencies = (
                    self.registry.get_more_concrete_factories(key)
                )
                ex.suggest_abstract_factories.extend(abstract_dependencies)
                ex.suggest_concrete_factories.extend(concrete_dependencies)
                raise

        return await compiled(
            self.parent_getter,
            self._exits,
            self._cache,
            self._context,
        )

    async def close(self, exception: BaseException | None = None) -> None:
        await self.__aexit__(None, exception, None)

    async def __aenter__(self) -> "AsyncContainer":
        return self

    async def __aexit__(  # noqa: C901
        self,
        exc_type: type[BaseException] | None = None,
        exception: BaseException | None = None,
        exc_tb: TracebackType | None = None,
    ) -> None:
        errors = None
        while self._exits:
            gen, agen = self._exits.pop()
            try:
                if agen is not None:
                    await agen.asend(exception)
                elif gen is not None:
                    gen.send(exception)
            except (StopIteration, StopAsyncIteration):
                pass
            except Exception as err:  # noqa: BLE001
                if errors is None:
                    errors = [err]
                else:
                    errors.append(err)
        self._cache = {}
        if self.parent_closer:
            try:
                await self.parent_closer(exc_type, exception, exc_tb)
            except Exception as err:  # noqa: BLE001
                if errors is None:
                    errors = [err]
                else:
                    errors.append(err)
        if errors:
            raise ExitError("Cleanup context errors", errors)  # noqa: TRY003

    async def _has(self, marker: Any) -> bool:
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
                parent_closer=container.__aexit__,
                parent_getter=container._get,  # noqa: SLF001
            )
    else:
        while container.registry.scope is not start_scope:
            container = AsyncContainer(
                *container.child_registries,
                parent_container=container,
                context=context,
                lock_factory=lock_factory,
                parent_closer=container.__aexit__,
                parent_getter=container._get,  # noqa: SLF001
            )
    return container


CONTAINER_KEY = DependencyKey(AsyncContainer, DEFAULT_COMPONENT)
