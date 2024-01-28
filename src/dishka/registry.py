from collections import defaultdict
from typing import Any, List, NewType, Type

from .dependency_source import Alias, Decorator, Factory
from .provider import Provider
from .scope import BaseScope


class Registry:
    __slots__ = ("scope", "_factories")

    def __init__(self, scope: BaseScope):
        self._factories: dict[Type, Factory] = {}
        self.scope = scope

    def add_provider(self, factory: Factory):
        self._factories[factory.provides] = factory

    def get_provider(self, dependency: Any) -> Factory:
        return self._factories.get(dependency)


def make_registries(
        *providers: Provider, scopes: Type[BaseScope],
) -> List[Registry]:
    dep_scopes = {}
    for provider in providers:
        for source in provider.dependency_sources:
            if hasattr(source, "scope"):
                dep_scopes[source.provides] = source.scope

    registries = {scope: Registry(scope) for scope in scopes}
    decorator_depth: dict[Type, int] = defaultdict(int)

    for provider in providers:
        for source in provider.dependency_sources:
            provides = source.provides
            if isinstance(source, Factory):
                scope = source.scope
            elif isinstance(source, Alias):
                scope = dep_scopes[source.source]
                dep_scopes[provides] = scope
                source = source.as_factory(scope)
            elif isinstance(source, Decorator):
                scope = dep_scopes[provides]
                registry = registries[scope]
                undecorated_type = NewType(
                    f"{provides.__name__}@{decorator_depth[provides]}",
                    source.provides,
                )
                decorator_depth[provides] += 1
                old_provider = registry.get_provider(provides)
                old_provider.provides = undecorated_type
                registry.add_provider(old_provider)
                source = source.as_factory(
                    scope, undecorated_type,
                )
            else:
                raise ValueError("Unknown dependency source type")
            registries[scope].add_provider(source)

    return list(registries.values())
