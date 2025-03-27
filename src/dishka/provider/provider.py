import inspect
from collections.abc import Callable, Sequence
from typing import Any, TypeGuard

from dishka.dependency_source import (
    Alias,
    CompositeDependencySource,
    ContextVariable,
    Decorator,
    DependencySource,
    Factory,
)
from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.scope import BaseScope
from .base_provider import BaseProvider, ProviderWrapper
from .exceptions import (
    NoScopeSetInContextError,
    NoScopeSetInProvideError,
)
from .make_alias import alias
from .make_context_var import from_context
from .make_decorator import decorate_on_instance
from .make_factory import (
    provide_all_on_instance,
    provide_on_instance,
)


def is_dependency_source(
    attribute: Any,
) -> TypeGuard[CompositeDependencySource]:
    return isinstance(attribute, CompositeDependencySource)


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

    def _name(self) -> str:
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
                    raise NoScopeSetInProvideError(
                        self._provides_name(source),
                        self._source_name(source),
                        self._name(),
                    )
                self.factories.append(source)
            if isinstance(source, Decorator):
                self.decorators.append(source)
            if isinstance(source, ContextVariable):
                if source.scope is None:
                    raise NoScopeSetInContextError(
                        self._provides_name(source),
                        self._name(),
                    )
                self.context_vars.append(source)

    def provide(
            self,
            source: Callable[..., Any] | type,
            *,
            scope: BaseScope | None = None,
            provides: Any = None,
            cache: bool = True,
            recursive: bool = False,
            override: bool = False,
    ) -> CompositeDependencySource:
        if scope is None:
            scope = self.scope
        composite = provide_on_instance(
            source=source,
            scope=scope,
            provides=provides,
            cache=cache,
            recursive=recursive,
            override=override,
        )
        self._add_dependency_sources(str(source), composite.dependency_sources)
        return composite

    def provide_all(
            self,
            *provides: Any,
            scope: BaseScope | None = None,
            cache: bool = True,
            recursive: bool = False,
            override: bool = False,
    ) -> CompositeDependencySource:
        if scope is None:
            scope = self.scope
        composite = provide_all_on_instance(
            *provides,
            scope=scope,
            cache=cache,
            recursive=recursive,
            override=override,
        )
        self._add_dependency_sources("?", composite.dependency_sources)
        return composite

    def alias(
            self,
            source: type,
            *,
            provides: Any = None,
            cache: bool = True,
            component: Component | None = None,
            override: bool = False,
    ) -> CompositeDependencySource:
        composite = alias(
            source=source,
            provides=provides,
            cache=cache,
            component=component,
            override=override,
        )
        self._add_dependency_sources(str(source), composite.dependency_sources)
        return composite

    def decorate(
            self,
            source: Callable[..., Any] | type,
            *,
            provides: Any = None,
    ) -> CompositeDependencySource:
        composite = decorate_on_instance(
            source=source,
            provides=provides,
        )
        self._add_dependency_sources(str(source), composite.dependency_sources)
        return composite

    def to_component(self, component: Component) -> ProviderWrapper:
        return ProviderWrapper(component, self)

    def from_context(
            self,
            provides: Any,
            *,
            scope: BaseScope | None = None,
            override: bool = False,
    ) -> CompositeDependencySource:
        composite = from_context(
            provides=provides,
            scope=scope or self.scope,
            override=override,
        )
        self._add_dependency_sources(
            name=str(provides),
            sources=composite.dependency_sources,
        )
        return composite
