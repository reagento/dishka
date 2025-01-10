from __future__ import annotations

from typing import Any

from dishka.entities.component import Component
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .factory import Factory


def _identity(x: Any) -> Any:
    return x


class Alias:
    __slots__ = ("cache", "component", "override", "provides", "source")

    def __init__(
            self, *,
            source: DependencyKey,
            provides: DependencyKey,
            cache: bool,
            override: bool,
    ) -> None:
        self.source = source
        self.provides = provides
        self.cache = cache
        self.override = override

    def as_factory(
            self, scope: BaseScope | None, component: Component | None,
    ) -> Factory:
        return Factory(
            scope=scope,
            source=_identity,
            provides=self.provides.with_component(component),
            is_to_bind=False,
            dependencies=[self.source.with_component(component)],
            kw_dependencies={},
            type_=FactoryType.ALIAS,
            cache=self.cache,
            override=self.override,
        )

    def __get__(self, instance: Any, owner: Any) -> Alias:
        return self
