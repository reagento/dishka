from typing import Any

from .scope import Scope
from .provider import DependencyProvider, Provider


class Registry:
    def __init__(self, scope: Scope):
        self._providers = {}
        self.scope = scope

    def add_provider(self, provider: DependencyProvider):
        self._providers[provider.result_type] = provider

    def get_provider(self, dependency: Any):
        return self._providers.get(dependency)


def make_registry(*providers: Provider, scope: Scope) -> Registry:
    registry = Registry(scope)
    for provider in providers:
        for dependency_provider in provider.dependencies.values():
            if dependency_provider.scope is scope:
                registry.add_provider(dependency_provider)
    return registry
