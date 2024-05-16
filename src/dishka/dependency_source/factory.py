from collections.abc import (
    Mapping,
    Sequence,
)
from enum import Enum
from typing import Any

from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope


class FactoryType(Enum):
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    FACTORY = "factory"
    ASYNC_FACTORY = "async_factory"
    VALUE = "value"
    ALIAS = "alias"
    CONTEXT = "context"


class Factory:
    __slots__ = (
        "dependencies", "kw_dependencies",
        "source", "provides", "scope", "type",
        "is_to_bind", "cache",
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
    ):
        self.dependencies = dependencies
        self.kw_dependencies = kw_dependencies
        self.source = source
        self.provides = provides
        self.scope = scope
        self.type = type_
        self.is_to_bind = is_to_bind
        self.cache = cache

    def __get__(self, instance, owner):
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
        )

    def with_component(self, component: Component) -> "Factory":
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
        )
