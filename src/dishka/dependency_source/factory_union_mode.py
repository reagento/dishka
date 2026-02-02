from typing import Any

from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope


class FactoryUnionMode:
    __slots__ = ("cache", "collect", "provides", "scope", "source")

    def __init__(
            self,
            *,
            source: DependencyKey,
            scope: BaseScope | None,
            collect: bool,
            cache: bool,
            provides: DependencyKey,
    ) -> None:
        self.source = source
        self.scope = scope
        self.collect = collect
        self.cache = cache
        self.provides = provides

    def with_component(self, component: Component) -> "FactoryUnionMode":
        return FactoryUnionMode(
            source=self.source.with_component(component),
            scope=self.scope,
            collect=self.collect,
            cache=self.cache,
            provides=self.provides.with_component(component),
        )

    def __get__(self, instance: Any, owner: Any) -> "FactoryUnionMode":
        return FactoryUnionMode(
            source=self.source,
            scope=self.scope,
            collect=self.collect,
            cache=self.cache,
            provides=self.provides,
        )
