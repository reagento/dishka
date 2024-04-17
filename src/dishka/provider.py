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
    from_context,
)
from .dependency_source.composite import CompositeDependencySource
from .dependency_source.make_decorator import decorate_on_instance
from .dependency_source.make_factory import (
    provide_all_on_instance,
    provide_on_instance,
)


def is_dependency_source(attribute: Any) -> bool:
    return isinstance(attribute, CompositeDependencySource)


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
        sources = inspect.getmembers(self, is_dependency_source)
        sources.sort(key=lambda s: s[1].number)
        for name, composite in sources:
            self._add_dependency_sources(name, composite.dependency_sources)

    def _name(self):
        if type(self) is Provider:
            return str(self)
        else:
            cls = type(self)
            return f"`{cls.__module__}.{cls.__qualname__}`"

    def _source_name(self, factory: Factory) -> str:
        source = factory.source
        if source == factory.provides.type_hint:
            return "`provides()`"
        elif func := getattr(source, "__func__", None):
            name = getattr(func, "__qualname__", None)
            if name:
                return f"`{name}`"
        elif isinstance(source, type):
            name = getattr(source, "__qualname__", None)
            if name:
                return f"`{source.__module__}.{name}`"
        else:
            name = getattr(source, "__qualname__", None)
            if name:
                return f"`{name}`"
        return str(source)

    def _provides_name(self, factory: Factory | ContextVariable) -> str:
        hint = factory.provides.type_hint
        name = getattr(hint, "__qualname__", None)
        if name:
            return f"`{hint.__module__}.{name}`"
        return str(hint)

    def _add_dependency_sources(
            self, name: str, sources: Sequence[DependencySource],
    ) -> None:
        for source in sources:
            if isinstance(source, Alias):
                self.aliases.append(source)
            if isinstance(source, Factory):
                if source.scope is None:
                    src_name = self._source_name(source)
                    provides_name = self._provides_name(source)
                    raise ValueError(
                        f"No scope is set for {provides_name}.\n"
                        f"Set in provide() call for {src_name} or "
                        f"within {self._name()}",
                    )
                self.factories.append(source)
            if isinstance(source, Decorator):
                self.decorators.append(source)
            if isinstance(source, ContextVariable):
                if source.scope is None:
                    provides_name = self._provides_name(source)
                    raise ValueError(
                        f"No scope is set for {provides_name}.\n"
                        f"Set in from_context() call or within {self._name()}",
                    )
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
        composite = provide_on_instance(
            source=source,
            scope=scope,
            provides=provides,
            cache=cache,
        )
        self._add_dependency_sources(str(source), composite.dependency_sources)
        return composite

    def provide_all(
            self,
            *provides: Any,
            scope: BaseScope | None = None,
            cache: bool = True,
    ) -> CompositeDependencySource:
        if scope is None:
            scope = self.scope
        composite = provide_all_on_instance(
            *provides, scope=scope, cache=cache,
        )
        self._add_dependency_sources("?", composite.dependency_sources)
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
        composite = decorate_on_instance(
            source=source,
            provides=provides,
        )
        self._add_dependency_sources(str(source), composite.dependency_sources)
        return composite

    def to_component(self, component: Component) -> "ProviderWrapper":
        return ProviderWrapper(component, self)

    def from_context(
            self, *, provides: Any, scope: BaseScope,
    ) -> CompositeDependencySource:
        composite = from_context(provides=provides, scope=scope)
        self._add_dependency_sources(str(provides),
                                     composite.dependency_sources)
        return composite


class ProviderWrapper(BaseProvider):
    def __init__(self, component: Component, provider: Provider) -> None:
        super().__init__(component)
        self.factories.extend(provider.factories)
        self.aliases.extend(provider.aliases)
        self.decorators.extend(provider.decorators)
