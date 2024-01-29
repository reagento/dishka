from collections import defaultdict
from typing import Any, List, NewType, Type

from .dependency_source import Factory
from .exceptions import InvalidGraphError
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
    dep_scopes: dict[Type, BaseScope] = {}
    alias_sources = {}
    for provider in providers:
        for source in provider.factories:
            dep_scopes[source.provides] = source.scope
        for source in provider.aliases:
            alias_sources[source.provides] = source.source

    registries = {scope: Registry(scope) for scope in scopes}
    decorator_depth: dict[Type, int] = defaultdict(int)

    for provider in providers:
        for source in provider.factories:
            scope = source.scope
            registries[scope].add_provider(source)
        for source in provider.aliases:
            alias_source = source.source
            visited_types = [alias_source]
            while alias_source not in dep_scopes:
                alias_source = alias_sources[alias_source]
                if alias_source in visited_types:
                    raise InvalidGraphError(
                        f"Cycle aliases detected {visited_types}",
                    )
                visited_types.append(alias_source)
            scope = dep_scopes[alias_source]
            dep_scopes[source.provides] = scope
            source = source.as_factory(scope)
            registries[scope].add_provider(source)
        for source in provider.decorators:
            provides = source.provides
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
            registries[scope].add_provider(source)

    return list(registries.values())
