from __future__ import annotations

from collections.abc import (
    Mapping,
    Sequence,
)
from typing import Any

from dishka.entities.component import Component
from dishka.entities.factory_type import FactoryData, FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import BaseMarker
from dishka.entities.scope import BaseScope


class Factory(FactoryData):
    __slots__ = (
        "cache",
        "connected_factories",
        "dependencies",
        "is_to_bind",
        "kw_dependencies",
        "when_active",
        "when_component",
        "when_dependencies",
        "when_override",
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
            when_override: BaseMarker | None,  # condition to override
            when_active: BaseMarker | None,  # condition to check availability
            when_component: Component | None,  # component of conditions
            when_dependencies: dict[DependencyKey, BaseMarker],  # conditional creation
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
        self.when_override = when_override
        self.when_active = when_active
        self.when_component = when_component
        self.when_dependencies: dict[DependencyKey, BaseMarker] = when_dependencies

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
            when_override=self.when_override,
            when_active=self.when_active,
            when_component=self.when_component,
            when_dependencies=self.when_dependencies,
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
            when_override=self.when_override,
            when_active=self.when_active,
            when_component=(component if self.when_component is None else self.when_component),
            when_dependencies=self.when_dependencies,
        )

    def with_scope(self, scope: BaseScope) -> Factory:
        return Factory(
            dependencies=tuple(self.dependencies),
            kw_dependencies=dict(self.kw_dependencies),
            source=self.source,
            provides=self.provides,
            scope=self.scope or scope,
            is_to_bind=self.is_to_bind,
            cache=self.cache,
            type_=self.type,
            when_override=self.when_override,
            when_active=self.when_active,
            when_component=self.when_component,
            when_dependencies=self.when_dependencies,
        )

    def replace(
        self,
        provides: DependencyKey | None = None,
    ) -> Factory:
        return Factory(
            dependencies=list(self.dependencies),
            kw_dependencies=dict(self.kw_dependencies),
            source=self.source,
            provides=provides or self.provides,
            scope=self.scope,
            is_to_bind=self.is_to_bind,
            cache=self.cache,
            type_=self.type,
            when_override=self.when_override,
            when_active=self.when_active,
            when_component=self.when_component,
            when_dependencies=self.when_dependencies,
        )

