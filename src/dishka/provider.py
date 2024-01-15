from enum import Enum
from typing import (
    Optional, Type, Callable, Union, Sequence, Any,
    get_type_hints, ClassVar, Dict,
)

from .scope import Scope


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
        if dep_provider and (
                dep_provider.scope == scope  # None scope is available
                or dep_provider.scope < scope
        ):
            return dep_provider
        return None

    def __init_subclass__(cls, **kwargs):
        cls.dependencies = {}
        for name, attr in vars(cls).items():
            if isinstance(attr, DependencyProvider):
                cls.dependencies[attr.result_type] = attr
