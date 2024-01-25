from typing import Any, List, Type

from .provider import DependencyProvider, Provider, Alias
from .scope import BaseScope


class Registry:
    __slots__ = ("scope", "_providers")

    def __init__(self, scope: BaseScope):
        self._providers = {}
        self.scope = scope

    def add_provider(self, provider: DependencyProvider):
        self._providers[provider.provides] = provider

    def get_provider(self, dependency: Any):
        return self._providers.get(dependency)


def make_registry(*providers: Provider, scope: BaseScope) -> Registry:
    registry = Registry(scope)
    for provider in providers:
        for dependency_provider in provider.dependency_providers.values():
            if dependency_provider.scope is scope:
                registry.add_provider(dependency_provider)

    for provider in providers:
        for alias in provider.aliases:
            dependency_provider = registry.get_provider(alias.source)
            if dependency_provider:
                registry.add_provider(
                    dependency_provider.aliased(alias.provides),
                )
    return registry


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
                dep_provider = dep_provider.as_provider(scope)
            else:
                raise
            registries[scope].add_provider(dep_provider)

    return list(registries.values())
