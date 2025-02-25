from dishka.dependency_source import (
    Alias,
    ContextVariable,
    Decorator,
    Factory,
)
from dishka.entities.component import Component


class BaseProvider:
    def __init__(self, component: Component | None) -> None:
        if component is not None:
            self.component = component
        self.factories: list[Factory] = []
        self.aliases: list[Alias] = []
        self.decorators: list[Decorator] = []
        self.context_vars: list[ContextVariable] = []


class ProviderWrapper(BaseProvider):
    def __init__(self, component: Component, provider: BaseProvider) -> None:
        super().__init__(component)
        self.factories.extend(provider.factories)
        self.aliases.extend(provider.aliases)
        self.decorators.extend(provider.decorators)
