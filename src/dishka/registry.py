from typing import Any, List, NewType, Type

from .provider import Alias, Decorator, DependencyProvider, Provider
from .scope import BaseScope


class Registry:
    __slots__ = ("scope", "_providers")

    def __init__(self, scope: BaseScope):
        self._providers = {}
        self.scope = scope

    def add_provider(self, provider: DependencyProvider):
        self._providers[provider.provides] = provider

    def get_provider(self, dependency: Any) -> DependencyProvider:
        return self._providers.get(dependency)


def make_registries(
        *providers: Provider, scopes: Type[BaseScope],
) -> List[Registry]:
    dep_scopes = {}
    for provider in providers:
        for dep_provider in provider.dependency_providers:
            if hasattr(dep_provider, "scope"):
                dep_scopes[dep_provider.provides] = dep_provider.scope

    registries = {scope: Registry(scope) for scope in scopes}

    for provider in providers:
        for dep_provider in provider.dependency_providers:
            if isinstance(dep_provider, DependencyProvider):
                scope = dep_provider.scope
            elif isinstance(dep_provider, Alias):
                scope = dep_scopes[dep_provider.source]
                dep_scopes[dep_provider.provides] = scope
                dep_provider = dep_provider.as_provider(scope)
            elif isinstance(dep_provider, Decorator):
                scope = dep_scopes[dep_provider.provides]
                registry = registries[scope]
                undecorated_type = NewType(
                    f"Old_{dep_provider.provides.__name__}",
                    dep_provider.provides,
                )
                old_provider = registry.get_provider(dep_provider.provides)
                old_provider.provides = undecorated_type
                registry.add_provider(old_provider)
                dep_provider = dep_provider.as_provider(
                    scope, undecorated_type,
                )
            else:
                raise
            registries[scope].add_provider(dep_provider)

    return list(registries.values())
