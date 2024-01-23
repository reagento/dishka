from typing import Any

from .provider import DependencyProvider, Provider
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
