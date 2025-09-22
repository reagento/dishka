from dishka.dependency_source import (
    Alias,
    ContextVariable,
    Decorator,
    Factory,
)
from dishka.entities.activator import ActivationFunc
from dishka.entities.component import Component


class BaseProvider:
    when: ActivationFunc | None = None
    component: Component | None = None

    def __init__(
        self,
        component: Component | None,
        when: ActivationFunc | None = None,
    ) -> None:
        if component is not None:
            self.component = component
        if when is not None:
            self.when = when
        self.factories: list[Factory] = []
        self.aliases: list[Alias] = []
        self.decorators: list[Decorator] = []
        self.context_vars: list[ContextVariable] = []


class ProviderWrapper(BaseProvider):
    def __init__(
        self,
        component: Component,
        provider: BaseProvider,
        when: ActivationFunc | None = None,
    ) -> None:
        super().__init__(component, when=when)
        self.factories.extend(provider.factories)
        self.aliases.extend(provider.aliases)
        self.decorators.extend(provider.decorators)
