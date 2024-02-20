import inspect
from typing import Any, Callable, List, Type

from .dependency_source import (
    Alias,
    Decorator,
    DependencySource,
    Factory,
    alias,
    decorate,
    provide,
)
from .exceptions import InvalidGraphError
from .scope import BaseScope


def is_dependency_source(attribute: Any) -> bool:
    return isinstance(attribute, DependencySource)


class Provider:
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

    def __init__(self, scope: BaseScope | None = None):
        self.factories: List[Factory] = []
        self.aliases: List[Alias] = []
        self.decorators: List[Decorator] = []
        self._init_dependency_sources()
        self.scope = self.scope or scope

    def _init_dependency_sources(self) -> None:
        processed_types = {}

        source: DependencySource
        for name, source in inspect.getmembers(self, is_dependency_source):
            if source.provides in processed_types:
                raise InvalidGraphError(
                    f"Type {source.provides} is registered multiple times "
                    f"in the same {Provider} by attributes "
                    f"{processed_types[source.provides]!r} and {name!r}",
                )
            if isinstance(source, Alias):
                self.aliases.append(source)
            if isinstance(source, Factory):
                self.factories.append(source)
            if isinstance(source, Decorator):
                self.decorators.append(source)
            processed_types[source.provides] = name

    def provide(
            self,
            source: Callable | Type,
            *,
            scope: BaseScope | None = None,
            provides: Any = None,
            cache: bool = True,
    ) -> Factory:
        if scope is None:
            scope = self.scope
        new_factory = provide(
            source=source,
            scope=scope,
            provides=provides,
            cache=cache,
        )
        self.factories.append(new_factory)
        return new_factory

    def alias(
            self,
            *,
            source: Type,
            provides: Type,
            cache: bool = True,
    ) -> Alias:
        new_alias = alias(
            source=source,
            provides=provides,
            cache=cache,
        )
        self.aliases.append(new_alias)
        return new_alias

    def decorate(
            self,
            source: Callable | Type,
            *,
            provides: Any = None,
    ) -> Decorator:
        new_decorator = decorate(
            source=source,
            provides=provides,
        )
        self.aliases.append(new_decorator)
        return new_decorator
