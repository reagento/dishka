from asyncio import Lock
from typing import (
    TypeVar, Optional, Type,
)

from .provider import DependencyProvider
from .registry import Registry, make_registry
from .scope import Scope

T = TypeVar("T")


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
        self._exit_stack = None
        if with_lock:
            self.lock = Lock()
        else:
            self.lock = None
        self.exits = []

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
            dependency_type: Type[T],
    ) -> T:
        sub_dependencies = [
            await self._get_unlocked(dependency)
            for dependency in dep_provider.dependencies
        ]
        if dep_provider.is_context:
            context_manager = dep_provider.callable(
                *sub_dependencies,
            )
            solved = await context_manager.__aenter__()
            self.exits.append(context_manager.__aexit__)
        else:
            solved = await dep_provider.callable(
                *sub_dependencies,
            )
        self.context[dependency_type] = solved
        return solved

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
        return await self._get_self(
            provider, dependency_type,
        )

    async def close(self):
        e = None
        for exit in self.exits:
            try:
                await exit(None, None, None)
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
