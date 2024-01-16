from contextlib import AsyncExitStack
from typing import (
    TypeVar, Optional, Type, )

from .provider import Provider, DependencyProvider
from .scope import Scope

T = TypeVar("T")


class AsyncContainer:
    def __init__(
            self, *providers: Provider,
            scope: Optional[Scope] = None,
            parent_container: Optional["AsyncContainer"] = None,
            context: Optional[dict] = None
    ):
        self.providers = providers
        self.context = {}
        if context:
            self.context.update(context)
        self.scope = scope
        self.parent_container = parent_container
        self.exit_stack = AsyncExitStack()

        if parent_container:
            if scope <= parent_container.scope:
                raise ValueError("Scope must only increase")

    def _get_child(self, context: Optional[dict] = None) -> "AsyncContainer":
        return AsyncContainer(
            *self.providers,
            scope=self.scope.next(),
            parent_container=self,
            context=context,
        )

    def __call__(self, context: Optional[dict] = None) -> "ContextWrapper":
        if not self.scope:
            raise ValueError("No root scope found, cannot enter context")
        return ContextWrapper(self._get_child(context))

    async def _get_parent(self, dependency_type: Type[T]) -> T:
        return await self.parent_container.get(dependency_type)

    async def _get_self(
            self,
            provider: Provider,
            dep_provider: DependencyProvider,
            dependency_type: Type[T],
    ) -> T:
        sub_dependencies = [
            await self.get(dependency)
            for dependency in dep_provider.dependencies
        ]
        context_manager = dep_provider.callable(
            provider, *sub_dependencies,
        )
        solved = await self.exit_stack.enter_async_context(context_manager)
        self.context[dependency_type] = solved
        return solved

    async def get(self, dependency_type: Type[T]) -> T:
        if dependency_type in self.context:
            return self.context[dependency_type]
        for provider in self.providers:
            dep_provider = provider.get_dependency_provider(
                dependency_type, self.scope,
            )
            if not dep_provider:
                continue
            if dep_provider.scope == self.scope:
                return await self._get_self(provider, dep_provider,
                                            dependency_type)
            elif dep_provider.scope > self.scope:
                raise ValueError("Cannot resolve dependency of greater scope")
            elif dep_provider.scope < self.scope:
                return await self._get_parent(dependency_type)

        raise ValueError(f"No provider found for {dependency_type!r} "
                         f"required for scope {self.scope}")

    async def close(self):
        await self.exit_stack.aclose()


class ContextWrapper:
    def __init__(self, container: AsyncContainer):
        self.container = container

    async def __aenter__(self) -> AsyncContainer:
        return self.container

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.container.close()
