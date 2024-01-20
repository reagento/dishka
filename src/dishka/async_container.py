from asyncio import Lock
from dataclasses import dataclass
from typing import (
    TypeVar, Optional, Type, Callable, List,
)

from .provider import DependencyProvider, ProviderType
from .registry import Registry, make_registry
from .scope import Scope

T = TypeVar("T")


@dataclass
class Exit:
    __slots__ = ("type", "callable")
    type: ProviderType
    callable: Callable


class AsyncContainer:
    def __init__(
            self,
            registry: Registry,
            *child_registries: Registry,
            parent_container: Optional["AsyncContainer"] = None,
            context: Optional[dict] = None,
            with_lock: bool = False,
    ):
        self.registry = registry
        self.child_registries = child_registries
        self.context = {}
        if context:
            self.context.update(context)
        self.parent_container = parent_container
        if with_lock:
            self.lock = Lock()
        else:
            self.lock = None
        self.exits: List[Exit] = []

    def _get_child(
            self,
            context: Optional[dict],
            with_lock: bool,
    ) -> "AsyncContainer":
        return AsyncContainer(
            *self.child_registries,
            parent_container=self,
            context=context,
            with_lock=with_lock,
        )

    def __call__(
            self,
            context: Optional[dict] = None,
            with_lock: bool = False,
    ) -> "AsyncContextWrapper":
        if not self.child_registries:
            raise ValueError("No child scopes found")
        return AsyncContextWrapper(self._get_child(context, with_lock))

    async def _get_parent(self, dependency_type: Type[T]) -> T:
        return await self.parent_container.get(dependency_type)

    async def _get_self(
            self,
            dep_provider: DependencyProvider,
    ) -> T:
        sub_dependencies = [
            await self._get_unlocked(dependency)
            for dependency in dep_provider.dependencies
        ]
        if dep_provider.type is ProviderType.GENERATOR:
            generator = dep_provider.callable(*sub_dependencies)
            self.exits.append(Exit(dep_provider.type, generator))
            return await next(generator)
        elif dep_provider.type is ProviderType.ASYNC_GENERATOR:
            generator = dep_provider.callable(*sub_dependencies)
            self.exits.append(Exit(dep_provider.type, generator))
            return await anext(generator)
        elif dep_provider.type is ProviderType.ASYNC_FACTORY:
            return await dep_provider.callable(*sub_dependencies)
        elif dep_provider.type is ProviderType.FACTORY:
            return dep_provider.callable(*sub_dependencies)
        elif dep_provider.type is ProviderType.VALUE:
            return dep_provider.callable
        else:
            raise ValueError(f"Unsupported type {dep_provider.type}")

    async def get(self, dependency_type: Type[T]) -> T:
        lock = self.lock
        if not lock:
            return await self._get_unlocked(dependency_type)
        async with lock:
            return await self._get_unlocked(dependency_type)

    async def _get_unlocked(self, dependency_type: Type[T]) -> T:
        if dependency_type in self.context:
            return self.context[dependency_type]
        provider = self.registry.get_provider(dependency_type)
        if not provider:
            if not self.parent_container:
                raise ValueError(f"No provider found for {dependency_type!r}")
            return await self.parent_container.get(dependency_type)
        solved = await self._get_self(provider)
        self.context[dependency_type] = solved
        return solved

    async def close(self):
        e = None
        for exit in self.exits:
            try:
                if exit.type is ProviderType.ASYNC_GENERATOR:
                    await anext(exit.callable)
                elif exit.type is ProviderType.GENERATOR:
                    next(exit.callable)
            except StopIteration:
                pass
            except StopAsyncIteration:
                pass
            except Exception as err:
                e = err
        if e:
            raise e


class AsyncContextWrapper:
    def __init__(self, container: AsyncContainer):
        self.container = container

    async def __aenter__(self) -> AsyncContainer:
        return self.container

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.container.close()


def make_async_container(*providers, scopes: Type[Scope], with_lock: bool = False) -> AsyncContainer:
    registries = [
        make_registry(*providers, scope=scope)
        for scope in scopes
    ]
    return AsyncContainer(*registries, with_lock=with_lock)
