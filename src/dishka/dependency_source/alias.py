from typing import (
    Any,
)

from ..component import Component
from ..scope import BaseScope
from .factory import Factory, FactoryType
from .key import DependencyKey


def _identity(x: Any) -> Any:
    return x


class Alias:
    __slots__ = ("source", "provides", "cache", "component")

    def __init__(
            self, *, source, provides, cache: bool,
            component: Component | None,
    ) -> None:
        self.source = DependencyKey(
            type_hint=source,
            component=component,
        )
        self.provides = provides
        self.cache = cache

    def as_factory(
            self, scope: BaseScope, component: Component,
    ) -> Factory:
        return Factory(
            scope=scope,
            source=_identity,
            provides=self.provides,
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
        source=source,
        provides=provides,
        cache=cache,
        component=component,
    )
