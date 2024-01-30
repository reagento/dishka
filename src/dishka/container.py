from dataclasses import dataclass
from threading import Lock
from typing import Callable, List, Optional, Type, TypeVar

from .dependency_source import Factory, FactoryType
from .exceptions import ExitExceptionGroup
from .provider import Provider
from .registry import Registry, make_registries
from .scope import BaseScope, Scope

T = TypeVar("T")


@dataclass
class Exit:
    __slots__ = ("type", "callable")
    type: FactoryType
    callable: Callable


class Container:
    __slots__ = (
        "registry", "child_registries", "context", "parent_container",
        "lock", "_exits",
    )

    def __init__(
            self,
            registry: Registry,
            *child_registries: Registry,
            parent_container: Optional["Container"] = None,
            context: Optional[dict] = None,
            lock_factory: Callable[[], Lock] | None = None,
    ):
        self.registry = registry
        self.child_registries = child_registries
        self.context = {type(self): self}
        if context:
            self.context.update(context)
        self.parent_container = parent_container
        if lock_factory:
            self.lock = lock_factory()
        else:
            self.lock = None
        self._exits: List[Exit] = []

    def _create_child(
            self,
            context: Optional[dict],
            lock_factory: Callable[[], Lock] | None,
    ) -> "Container":
        return Container(
            *self.child_registries,
            parent_container=self,
            context=context,
            lock_factory=lock_factory,
        )

    def __call__(
            self,
            context: Optional[dict] = None,
            lock_factory: Callable[[], Lock] | None = None,
    ) -> "ContextWrapper":
        """
        Prepare container for entering the inner scope.
        :param context: Data which will available in inner scope
        :param lock_factory: Callable to create lock instance or None
        :return: context manager for inner scope
        """
        if not self.child_registries:
            raise ValueError("No child scopes found")
        return ContextWrapper(self._create_child(context, lock_factory))

    def _get_from_self(self, factory: Factory) -> T:
        sub_dependencies = [
            self._get_unlocked(dependency)
            for dependency in factory.dependencies
        ]
        if factory.type is FactoryType.GENERATOR:
            generator = factory.source(*sub_dependencies)
            self._exits.append(Exit(factory.type, generator))
            return next(generator)
        elif factory.type is FactoryType.FACTORY:
            return factory.source(*sub_dependencies)
        elif factory.type is FactoryType.VALUE:
            return factory.source
        else:
            raise ValueError(f"Unsupported type {factory.type}")

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
        solved = self._get_from_self(provider)
        self.context[dependency_type] = solved
        return solved

    def close(self) -> None:
        errors = []
        for exit_generator in self._exits[::-1]:
            try:
                if exit_generator.type is FactoryType.GENERATOR:
                    next(exit_generator.callable)
            except StopIteration:
                pass
            except Exception as err:  # noqa: BLE001
                errors.append(err)
        if errors:
            raise ExitExceptionGroup("Cleanup context errors", errors)


class ContextWrapper:
    __slots__ = ("container",)

    def __init__(self, container: Container):
        self.container = container

    def __enter__(self) -> Container:
        return self.container

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.close()


def make_container(
        *providers: Provider,
        scopes: Type[BaseScope] = Scope,
        context: Optional[dict] = None,
        lock_factory: Callable[[], Lock] | None = None,
) -> ContextWrapper:
    registries = make_registries(*providers, scopes=scopes)
    return ContextWrapper(
        Container(*registries, context=context, lock_factory=lock_factory),
    )
