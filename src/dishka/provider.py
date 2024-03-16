import inspect
from collections.abc import Callable, Sequence
from typing import Any

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.scope import BaseScope
from .dependency_source import (
    Alias,
    ContextVariable,
    Decorator,
    DependencySource,
    Factory,
    alias,
    decorate,
    from_context,
    provide,
)
from .dependency_source.composite import CompositeDependencySource


def is_dependency_source(attribute: Any) -> bool:
    return isinstance(attribute, DependencySource | CompositeDependencySource)


class BaseProvider:
    def __init__(self, component: Component):
        if component is not None:
            self.component = component
        self.factories: list[Factory] = []
        self.aliases: list[Alias] = []
        self.decorators: list[Decorator] = []
        self.context_vars: list[ContextVariable] = []


class Provider(BaseProvider):
    """
    A collection of dependency sources.

    Inherit this class and add attributes using
    `provide`, `alias` or `decorate`.

    You can use `__init__`, regular methods and attributes as usual,
    they won't be analyzed when creating a container

    The only intended usage of providers is to pass them when
    creating a container
    """
    scope: BaseScope | None = None
    component: Component = DEFAULT_COMPONENT

    def __init__(
            self,
            scope: BaseScope | None = None,
            component: Component | None = None,
    ):
        super().__init__(component)
        self.scope = self.scope or scope
        self._init_dependency_sources()

    def _init_dependency_sources(self) -> None:
        for name, composite in inspect.getmembers(self, is_dependency_source):
            if isinstance(composite, CompositeDependencySource):
                sources = composite.dependency_sources
            else:
                sources = [composite]
            self._add_dependency_sources(name, sources)

    def _add_dependency_sources(
            self, name: str, sources: Sequence[DependencySource],
    ) -> None:
        for source in sources:
            if isinstance(source, Alias):
                self.aliases.append(source)
            if isinstance(source, Factory):
                self.factories.append(source)
            if isinstance(source, Decorator):
                self.decorators.append(source)
            if isinstance(source, ContextVariable):
                self.context_vars.append(source)

    def provide(
            self,
            source: Callable | type,
            *,
            scope: BaseScope | None = None,
            provides: Any = None,
            cache: bool = True,
    ) -> CompositeDependencySource:
        if scope is None:
            scope = self.scope
        composite = provide(
            source=source,
            scope=scope,
            provides=provides,
            cache=cache,
        )
        self._add_dependency_sources(str(source), composite.dependency_sources)
        return composite

    def alias(
            self,
            *,
            source: type,
            provides: Any,
            cache: bool = True,
    ) -> CompositeDependencySource:
        composite = alias(
            source=source,
            provides=provides,
            cache=cache,
        )
        self._add_dependency_sources(str(source), composite.dependency_sources)
        return composite

    def decorate(
            self,
            source: Callable | type,
            *,
            provides: Any = None,
    ) -> CompositeDependencySource:
        composite = decorate(
            source=source,
            provides=provides,
        )
        self._add_dependency_sources(str(source), composite.dependency_sources)
        return composite

    def to_component(self, component: Component) -> "ProviderWrapper":
        return ProviderWrapper(component, self)

    def from_context(
            self, *, provides: Any, scope: BaseScope,
    ) -> ContextVariable:
        context_var = from_context(provides=provides, scope=scope)
        self.context_vars.append(context_var)
        return context_var


class ProviderWrapper(BaseProvider):
    def __init__(self, component: Component, provider: Provider) -> None:
        super().__init__(component)
        self.factories.extend(provider.factories)
        self.aliases.extend(provider.aliases)
        self.decorators.extend(provider.decorators)
