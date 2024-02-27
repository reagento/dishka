from asyncio import Lock
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional, TypeVar

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope, Scope
from .dependency_source import Factory, FactoryType
from .exceptions import (
    ExitError,
    NoFactoryError,
    UnsupportedFactoryError,
)
from .provider import Provider
from .registry import Registry, make_registries

T = TypeVar("T")


@dataclass
class Exit:
    __slots__ = ("type", "callable")
    type: FactoryType
    callable: Callable


class AsyncContainer:
    __slots__ = (
        "registry", "child_registries", "context", "parent_container",
        "lock", "_exits",
    )

    def __init__(
            self,
            registry: Registry,
            *child_registries: Registry,
            parent_container: Optional["AsyncContainer"] = None,
            context: dict | None = None,
            lock_factory: Callable[[], Lock] | None = None,
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

    def _create_child(
            self,
            context: dict | None,
            lock_factory: Callable[[], Lock] | None,
    ) -> "AsyncContainer":
        return AsyncContainer(
            *self.child_registries,
            parent_container=self,
            context=context,
            lock_factory=lock_factory,
        )

    def __call__(
            self,
            context: dict | None = None,
            lock_factory: Callable[[], Lock] | None = None,
    ) -> "AsyncContextWrapper":
        """
        Prepare container for entering the inner scope.
        :param context: Data which will available in inner scope
        :param lock_factory: Callable to create lock instance or None
        :return: async context manager for inner scope
        """
        if not self.child_registries:
            raise ValueError("No child scopes found")
        return AsyncContextWrapper(self._create_child(context, lock_factory))

    async def _get_from_self(
            self, factory: Factory, key: DependencyKey,
    ) -> T:
        try:
            sub_dependencies = [
                await self._get_unlocked(dependency)
                for dependency in factory.dependencies
            ]
        except NoFactoryError as e:
            e.add_path(key)
            raise

        if factory.type is FactoryType.GENERATOR:
            generator = factory.source(*sub_dependencies)
            self._exits.append(Exit(factory.type, generator))
            solved = next(generator)
        elif factory.type is FactoryType.FACTORY:
            solved = factory.source(*sub_dependencies)
        elif factory.type is FactoryType.ASYNC_GENERATOR:
            generator = factory.source(*sub_dependencies)
            self._exits.append(Exit(factory.type, generator))
            solved = await anext(generator)
        elif factory.type is FactoryType.ASYNC_FACTORY:
            solved = await factory.source(*sub_dependencies)
        elif factory.type is FactoryType.VALUE:
            solved = factory.source
        else:
            raise UnsupportedFactoryError(
                f"Unsupported factory type {factory.type}.",
            )
        if factory.cache:
            self.context[key] = solved
        return solved

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

    async def _get_unlocked(self, key: DependencyKey) -> Any:
        if key in self.context:
            return self.context[key]
        factory = self.registry.get_factory(key)
        if not factory:
            if not self.parent_container:
                raise NoFactoryError(key)
            return await self.parent_container.get(
                key.type_hint, key.component,
            )
        return await self._get_from_self(factory, key)

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
        *providers: Provider,
        scopes: type[BaseScope] = Scope,
        context: dict | None = None,
        lock_factory: Callable[[], Lock] | None = Lock,
) -> AsyncContainer:
    registries = make_registries(*providers, scopes=scopes)
    return AsyncContainer(
        *registries,
        context=context,
        lock_factory=lock_factory,
    )
