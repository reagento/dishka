from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from typing import Any

from dishka.entities.activator import ActivationFunc
from dishka.entities.component import Component
from dishka.entities.factory_type import FactoryData, FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope


class Factory(FactoryData):
    __slots__ = (
        "cache",
        "dependencies",
        "is_to_bind",
        "kw_dependencies",
        "override",
        "when",
    )

    def __init__(
            self,
            *,
            dependencies: Sequence[DependencyKey],
            kw_dependencies: Mapping[str, DependencyKey],
            source: Any,
            provides: DependencyKey,
            scope: BaseScope | None,
            type_: FactoryType,
            is_to_bind: bool,
            cache: bool,
            override: bool,
            when: ActivationFunc | None,
    ) -> None:
        super().__init__(
            source=source,
            provides=provides,
            type_=type_,
            scope=scope,
        )
        self.dependencies = dependencies
        self.kw_dependencies = kw_dependencies
        self.is_to_bind = is_to_bind
        self.cache = cache
        self.override = override
        self.when = when

    def __get__(self, instance: Any, owner: Any) -> Factory:
        scope = self.scope or instance.scope
        if instance is None:
            return self
        if self.is_to_bind:
            source = self.source.__get__(instance, owner)
            dependencies = self.dependencies[1:]
        else:
            source = self.source
            dependencies = self.dependencies[:]
        return Factory(
            dependencies=dependencies,
            kw_dependencies=self.kw_dependencies,
            source=source,
            provides=self.provides,
            scope=scope,
            type_=self.type,
            is_to_bind=False,
            cache=self.cache,
            override=self.override,
            when=self.when,
        )

    def with_component(self, component: Component) -> Factory:
        return Factory(
            dependencies=[
                d.with_component(component) for d in self.dependencies
            ],
            kw_dependencies={
                name: d.with_component(component)
                for name, d in self.kw_dependencies.items()
            },
            source=self.source,
            provides=self.provides.with_component(component),
            scope=self.scope,
            is_to_bind=self.is_to_bind,
            cache=self.cache,
            type_=self.type,
            override=self.override,
            when=self.when,
        )
