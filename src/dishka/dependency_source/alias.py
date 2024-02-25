from typing import (
    Any,
)

from dishka.component import Component
from dishka.scope import BaseScope
from .factory import Factory, FactoryType
from .key import DependencyKey


def _identity(x: Any) -> Any:
    return x


class Alias:
    __slots__ = ("source", "provides", "cache", "component")

    def __init__(
            self, *,
            source: DependencyKey,
            provides: DependencyKey,
            cache: bool,
    ) -> None:
        self.source = source
        self.provides = provides
        self.cache = cache

    def as_factory(
            self, scope: BaseScope, component: Component,
    ) -> Factory:
        return Factory(
            scope=scope,
            source=_identity,
            provides=self.provides.with_component(component),
            is_to_bind=False,
            dependencies=[self.source.with_component(component)],
            type_=FactoryType.FACTORY,
            cache=self.cache,
        )

    def __get__(self, instance, owner):
        return self


def alias(
        *,
        source: type,
        provides: type,
        cache: bool = True,
        component: Component | None = None,
) -> Alias:
    return Alias(
        source=DependencyKey(
            type_hint=source,
            component=component,
        ),
        provides=DependencyKey(provides),
        cache=cache,
    )
