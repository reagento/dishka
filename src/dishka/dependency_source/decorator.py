from __future__ import annotations

from typing import Any, TypeVar, get_origin

from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .factory import Factory
from .type_match import is_broader_or_same_type


class Decorator:
    __slots__ = ("provides", "factory")

    def __init__(
            self,
            factory: Factory,
            provides: DependencyKey | None = None,
    ) -> None:
        self.factory = factory
        if provides:
            self.provides = provides
        else:
            self.provides = factory.provides

    def is_generic(self):
        return (
            isinstance(self.provides.type_hint, TypeVar)
            or get_origin(self.provides.type_hint) is not None
        )

    def match_type(self, type_: Any) -> bool:
        return is_broader_or_same_type(self.provides.type_hint, type_)

    def as_factory(
            self, *,
            scope: BaseScope,
            new_dependency: DependencyKey,
            cache: bool,
            component: Component,
    ) -> Factory:
        return Factory(
            scope=scope,
            source=self.factory.source,
            provides=self.factory.provides.with_component(component),
            is_to_bind=self.factory.is_to_bind,
            dependencies=[
                (
                    new_dependency
                    if dep.type_hint == self.provides.type_hint
                    else dep
                ).with_component(component)
                for dep in self.factory.dependencies
            ],
            kw_dependencies={
                name: (
                    new_dependency
                    if dep.type_hint == self.provides.type_hint
                    else dep
                ).with_component(component)
                for name, dep in self.factory.kw_dependencies.items()
            },
            type_=self.factory.type,
            cache=cache,
            override=False,
        )

    def __get__(self, instance: Any, owner: Any) -> Decorator:
        return Decorator(self.factory.__get__(instance, owner))
