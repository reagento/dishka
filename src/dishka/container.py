from contextlib import ExitStack
from threading import Lock
from typing import (
    TypeVar, Optional, Type, )

from .provider import Provider, DependencyProvider
from .scope import Scope

T = TypeVar("T")


class Container:
    def __init__(
            self, *providers: Provider,
            scope: Optional[Scope] = None,
            parent_container: Optional["Container"] = None,
            context: Optional[dict] = None,
            with_lock: bool = False,
    ):
        self.providers = providers
        self.context = {}
        if context:
            self.context.update(context)
        self.scope = scope
        self.parent_container = parent_container
        self.exit_stack = ExitStack()
        if with_lock:
            self.lock = Lock()
        else:
            self.lock = None

        if parent_container:
            if scope <= parent_container.scope:
                raise ValueError("Scope must only increase")

    def _get_child(
            self,
            context: Optional[dict],
            with_lock: bool,
    ) -> "Container":
        return Container(
            *self.providers,
            scope=self.scope.next(),
            parent_container=self,
            context=context,
            with_lock=with_lock,
        )

    def __call__(
            self,
            context: Optional[dict] = None,
            with_lock: bool = False,
    ) -> "ContextWrapper":
        if not self.scope:
            raise ValueError("No root scope found, cannot enter context")
        return ContextWrapper(self._get_child(context, with_lock))

    def _get_parent(self, dependency_type: Type[T]) -> T:
        return self.parent_container.get(dependency_type)

    def _get_self(
            self,
            provider: Provider,
            dep_provider: DependencyProvider,
            dependency_type: Type[T],
    ) -> T:
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

    def get(self, dependency_type: Type[T]) -> T:
        if self.lock:
            self.lock.acquire()
        try:
            if dependency_type in self.context:
                return self.context[dependency_type]
            for provider in self.providers:
                dep_provider = provider.get_dependency_provider(
                    dependency_type, self.scope,
                )
                if not dep_provider:
                    continue
                if dep_provider.scope == self.scope:
                    return self._get_self(
                        provider, dep_provider, dependency_type,
                    )
                elif dep_provider.scope > self.scope:
                    raise ValueError(
                        "Cannot resolve dependency of greater scope",
                    )
                elif dep_provider.scope < self.scope:
                    return self._get_parent(dependency_type)

            raise ValueError(f"No provider found for {dependency_type!r} "
                             f"required for scope {self.scope}")
        finally:
            if self.lock:
                self.lock.release()

    def close(self):
        self.exit_stack.close()


class ContextWrapper:
    def __init__(self, container: Container):
        self.container = container

    def __enter__(self) -> Container:
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.close()
