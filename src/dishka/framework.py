from contextlib import ExitStack
from enum import Enum
from functools import total_ordering
from typing import (
    TypeVar, Optional, Type, Callable, Union, Sequence, Any,
    get_type_hints, ClassVar, Dict,
)


@total_ordering
class Scope(Enum):
    def __lt__(self, other) -> bool:
        if other is None:
            return False

        items = list(type(self))
        return items.index(self) < items.index(other)

    def next(self):
        items = list(type(self))
        return items[items.index(self) + 1]


class DependencyProvider:
    def __init__(
            self,
            dependencies: Sequence,
            callable: Callable,
            result_type: Type,
            scope: Scope,
    ):
        self.dependencies = dependencies
        self.callable = callable
        self.result_type = result_type
        self.scope = scope


def make_dependency_provider(scope: Optional[Scope], func: Callable):
    hints = get_type_hints(func, include_extras=True)
    return DependencyProvider(
        dependencies=[
            value
            for name, value in hints.items()
            if name != "return"
        ],
        callable=func,
        scope=scope,
        result_type=hints["return"],
    )


def provide(scope_or_func: Union[Scope, Callable]):
    if not isinstance(scope_or_func, Enum):
        return make_dependency_provider(None, scope_or_func)

    def scoped(func):
        return make_dependency_provider(scope_or_func, func)

    return scoped


class Provider:
    dependencies: ClassVar[Dict[Any, DependencyProvider]]

    def get_dependency_provider(
            self, dependency: Any, scope: Scope,
    ) -> Optional[DependencyProvider]:
        dep_provider = self.dependencies.get(dependency)
        if dep_provider and dep_provider.scope <= scope:
            return dep_provider
        return None

    def __init_subclass__(cls, **kwargs):
        cls.dependencies = {}
        for name, attr in vars(cls).items():
            if isinstance(attr, DependencyProvider):
                cls.dependencies[attr.result_type] = attr


T = TypeVar("T")


class Container:
    def __init__(
            self, *providers: Provider,
            scope: Optional[Scope] = None,
            parent_container: Optional["Container"] = None,
    ):
        self.providers = providers
        self.context = {}
        self.scope = scope
        self.parent_container = parent_container
        self.exit_stack = ExitStack()

        if parent_container:
            if scope <= parent_container.scope:
                raise ValueError("Scope must only increase")

    def __call__(self) -> "Container":
        return Container(
            *self.providers,
            scope=self.scope.next(),
            parent_container=self,
        )

    def get(self, dependency_type: Type[T]) -> T:
        if dependency_type in self.context:
            return self.context[dependency_type]
        for provider in self.providers:
            dep_provider = provider.get_dependency_provider(
                dependency_type, self.scope,
            )
            if not dep_provider:
                continue
            if dep_provider.scope > self.scope:
                raise ValueError("Cannot resolve dependency of greater scope")
            if dep_provider.scope < self.scope:
                return self.parent_container.get(dependency_type)

            sub_dependencies = [
                self.get(dependency)
                for dependency in dep_provider.dependencies
            ]
            context_manager = dep_provider.callable(provider,
                                                    *sub_dependencies)
            solved = self.exit_stack.enter_context(context_manager)
            self.context[dependency_type] = solved
            return solved

        raise ValueError(f"No provider found for {dependency_type!r}")

    def __enter__(self):
        return self.__call__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.exit_stack.close()
