from asyncio import Lock
from collections.abc import Callable
from contextlib import suppress
from typing import Any, Iterable, Literal, Optional, TypeVar, overload

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope, Scope
from .container_objects import Exit
from .dependency_source import FactoryType
from .exceptions import (
    ExitError,
    NoContextValueError,
    NoFactoryError,
)
from .provider import BaseProvider
from .registry import Registry, RegistryBuilder

T = TypeVar("T")


class AsyncContainer:
    __slots__ = (
        "registry", "child_registries", "context", "parent_container",
        "lock", "_exits", "close_parent",
    )

    def __init__(
            self,
            registry: Registry,
            *child_registries: Registry,
            parent_container: Optional["AsyncContainer"] = None,
            context: dict | None = None,
            lock_factory: Callable[[], Lock] | None = None,
            close_parent: bool = False,
    ):
        self.registry = registry
        self.child_registries = child_registries
        self.context = {DependencyKey(type(self), DEFAULT_COMPONENT): self}
        if context:
            for key, value in context.items():
                if isinstance(key, DependencyKey):
                    self.context[key] = value
                else:
                    self.context[DependencyKey(key, DEFAULT_COMPONENT)] = value

        self.parent_container = parent_container
        if lock_factory:
            self.lock = lock_factory()
        else:
            self.lock = None
        self._exits: list[Exit] = []
        self.close_parent = close_parent

    def __call__(
            self,
            context: dict | None = None,
            lock_factory: Callable[[], Lock] | None = None,
            scope: BaseScope | None = None,
    ) -> "AsyncContextWrapper":
        """
        Prepare container for entering the inner scope.
        :param context: Data which will available in inner scope
        :param lock_factory: Callable to create lock instance or None
        :param scope: target scope or None to enter next non-skipped scope
        :return: async context manager for inner scope
        """
        if not self.child_registries:
            raise ValueError("No child scopes found")

        child = AsyncContainer(
            *self.child_registries,
            parent_container=self,
            context=context,
            lock_factory=lock_factory,
        )
        if scope is None:
            while child.registry.scope.skip:
                if not child.child_registries:
                    raise ValueError("No non-skipped scopes found.")
                child = AsyncContainer(
                    *child.child_registries,
                    parent_container=child,
                    context=context,
                    lock_factory=lock_factory,
                    close_parent=True,
                )
        else:
            while child.registry.scope is not scope:
                if not child.child_registries:
                    raise ValueError(f"Cannot find {scope} as a child of "
                                     f"current {self.registry.scope}")
                child = AsyncContainer(
                    *child.child_registries,
                    parent_container=child,
                    context=context,
                    lock_factory=lock_factory,
                    close_parent=True,
                )
        return AsyncContextWrapper(child)

    async def get(
            self,
            dependency_type: type[T],
            component: Component = DEFAULT_COMPONENT,
    ) -> T:
        lock = self.lock
        key = DependencyKey(dependency_type, component)
        if not lock:
            return await self._get_unlocked(key)
        async with lock:
            return await self._get_unlocked(key)

    @overload
    async def resolve_all(self, components: None = None) -> None: ...
    @overload
    async def resolve_all(self, components: Literal[True]) -> None: ...
    @overload
    async def resolve_all(self, components: Iterable[Component]) -> None: ...

    async def resolve_all(self, components: Any = None) -> None:
        """
        Resolve all container dependencies in the current scope for the given
        components.

        Examples:
            >>> container.resolve_all()
            Resolve all dependencies for the default component.

            >>> container.resolve_all(True)
            Resolve all dependencies for all components.

            >>> container.resolve_all(['component1', 'component2'])
            Resolve dependencies for 'component1' and 'component2'.
        """
        if not components:

            def component_check(k: DependencyKey) -> bool:
                return k.component == DEFAULT_COMPONENT
        elif components is True:

            def component_check(k: DependencyKey) -> bool:
                return True
        else:

            def component_check(k: DependencyKey) -> bool:
                return k.component in components

        for key in filter(component_check, self.registry.factories):
            with suppress(NoContextValueError):
                await self._get_unlocked(key)

    async def _get_unlocked(self, key: DependencyKey) -> Any:
        if key in self.context:
            return self.context[key]
        compiled = self.registry.get_compiled_async(key)
        if not compiled:
            if not self.parent_container:
                raise NoFactoryError(key)
            return await self.parent_container.get(
                key.type_hint, key.component,
            )
        try:
            return await compiled(self._get_unlocked, self._exits,
                                  self.context)
        except NoFactoryError as e:
            e.add_path(self.registry.get_factory(key))
            raise

    async def close(self):
        errors = []
        for exit_generator in self._exits[::-1]:
            try:
                if exit_generator.type is FactoryType.ASYNC_GENERATOR:
                    await anext(exit_generator.callable)
                elif exit_generator.type is FactoryType.GENERATOR:
                    next(exit_generator.callable)
            except StopIteration:  # noqa: PERF203
                pass
            except StopAsyncIteration:
                pass
            except Exception as err:  # noqa: BLE001
                errors.append(err)
        if self.close_parent:
            try:
                await self.parent_container.close()
            except Exception as err:  # noqa: BLE001
                errors.append(err)
        if errors:
            raise ExitError("Cleanup context errors", errors)


class AsyncContextWrapper:
    def __init__(self, container: AsyncContainer):
        self.container = container

    async def __aenter__(self) -> AsyncContainer:
        return self.container

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.container.close()


def make_async_container(
        *providers: BaseProvider,
        scopes: type[BaseScope] = Scope,
        context: dict | None = None,
        lock_factory: Callable[[], Lock] | None = Lock,
        skip_validation: bool = False,
        start_scope: BaseScope | None = None,
) -> AsyncContainer:
    registries = RegistryBuilder(
        scopes=scopes,
        container_type=AsyncContainer,
        providers=providers,
        skip_validation=skip_validation,
    ).build()
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
