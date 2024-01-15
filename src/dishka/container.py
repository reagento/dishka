from contextlib import ExitStack
from typing import (
    TypeVar, Optional, Type, )

from .provider import Provider
from .scope import Scope

T = TypeVar("T")


class Container:
    def __init__(
            self, *providers: Provider,
            scope: Optional[Scope] = None,
            parent_container: Optional["Container"] = None,
            context: Optional[dict] = None
    ):
        self.providers = providers
        self.context = {}
        if context:
            self.context.update(context)
        self.scope = scope
        self.parent_container = parent_container
        self.exit_stack = ExitStack()
        self.child: Optional["Container"] = None

        if parent_container:
            if scope <= parent_container.scope:
                raise ValueError("Scope must only increase")

    def _get_child(self, context: Optional[dict] = None) -> "Container":
        return Container(
            *self.providers,
            scope=self.scope.next(),
            parent_container=self,
            context=context,
        )

    def __call__(self, context: Optional[dict] = None) -> "ContextWrapper":
        return ContextWrapper(self._get_child(context))

    def get(self, dependency_type: Type[T]) -> T:
        if dependency_type in self.context:
            return self.context[dependency_type]
        for provider in self.providers:
            dep_provider = provider.get_dependency_provider(
                dependency_type, self.scope,
            )
            if not dep_provider:
                continue
            if dep_provider.scope == self.scope:
                pass
            elif dep_provider.scope > self.scope:
                raise ValueError("Cannot resolve dependency of greater scope")
            elif dep_provider.scope < self.scope:
                return self.parent_container.get(dependency_type)

            sub_dependencies = [
                self.get(dependency)
                for dependency in dep_provider.dependencies
            ]
            context_manager = dep_provider.callable(
                provider, *sub_dependencies,
            )
            solved = self.exit_stack.enter_context(context_manager)
            self.context[dependency_type] = solved
            return solved

        raise ValueError(f"No provider found for {dependency_type!r}")

    def close(self):
        self.exit_stack.close()


class ContextWrapper:
    def __init__(self, container: Container):
        self.container = container

    def __enter__(self) -> Container:
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.close()
