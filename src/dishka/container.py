from threading import Lock
from typing import Optional, Type, TypeVar

from .provider import DependencyProvider, ProviderType
from .registry import Registry, make_registry
from .scope import BaseScope, Scope

T = TypeVar("T")


class Container:
    __slots__ = (
        "registry", "child_registries", "context", "parent_container",
        "lock", "exits",
    )

    def __init__(
            self,
            registry: Registry,
            *child_registries: Registry,
            parent_container: Optional["Container"] = None,
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
        self.exits = []

    def _get_child(
            self,
            context: Optional[dict],
            with_lock: bool,
    ) -> "Container":
        return Container(
            *self.child_registries,
            parent_container=self,
            context=context,
            with_lock=with_lock,
        )

    def __call__(
            self,
            context: Optional[dict] = None,
            with_lock: bool = False,
    ) -> "ContextWrapper":
        if not self.child_registries:
            raise ValueError("No child scopes found")
        return ContextWrapper(self._get_child(context, with_lock))

    def _get_parent(self, dependency_type: Type[T]) -> T:
        return self.parent_container.get(dependency_type)

    def _get_self(
            self,
            dep_provider: DependencyProvider,
    ) -> T:
        sub_dependencies = [
            self._get_unlocked(dependency)
            for dependency in dep_provider.dependencies
        ]
        if dep_provider.type is ProviderType.GENERATOR:
            generator = dep_provider.callable(*sub_dependencies)
            self.exits.append(generator)
            return next(generator)
        elif dep_provider.type is ProviderType.FACTORY:
            return dep_provider.callable(*sub_dependencies)
        elif dep_provider.type is ProviderType.VALUE:
            return dep_provider.callable
        else:
            raise ValueError(f"Unsupported type {dep_provider.type}")

    def get(self, dependency_type: Type[T]) -> T:
        lock = self.lock
        if not lock:
            return self._get_unlocked(dependency_type)
        with lock:
            return self._get_unlocked(dependency_type)

    def _get_unlocked(self, dependency_type: Type[T]) -> T:
        if dependency_type in self.context:
            return self.context[dependency_type]
        provider = self.registry.get_provider(dependency_type)
        if not provider:
            if not self.parent_container:
                raise ValueError(f"No provider found for {dependency_type!r}")
            return self.parent_container.get(dependency_type)
        solved = self._get_self(provider)
        self.context[dependency_type] = solved
        return solved

    def close(self):
        e = None
        for exit in self.exits:
            try:
                next(exit)
            except StopIteration:
                pass
            except Exception as err:
                e = err
        if e:
            raise e


class ContextWrapper:
    def __init__(self, container: Container):
        self.container = container

    def __enter__(self) -> Container:
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.close()


def make_container(
        *providers,
        scopes: Type[BaseScope] = Scope,
        context: Optional[dict] = None,
        with_lock: bool = False,
) -> ContextWrapper:
    registries = [
        make_registry(*providers, scope=scope)
        for scope in scopes
    ]
    return ContextWrapper(
        Container(*registries, context=context, with_lock=with_lock)
    )
