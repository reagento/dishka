from __future__ import annotations

from typing import Any, NoReturn

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .alias import Alias
from .factory import Factory


def context_stub() -> NoReturn:
    raise NotImplementedError


class ContextVariable:
    __slots__ = ("override", "provides", "scope")

    def __init__(
            self, *,
            provides: DependencyKey,
            scope: BaseScope | None,
            override: bool,
    ) -> None:
        self.provides = provides
        self.scope = scope
        self.override = override

    def as_factory(
            self, component: Component,
    ) -> Factory:
        if component == DEFAULT_COMPONENT:
            return Factory(
                scope=self.scope,
                source=context_stub,
                provides=self.provides,
                is_to_bind=False,
                dependencies=[],
                kw_dependencies={},
                type_=FactoryType.CONTEXT,
                cache=False,
                override=self.override,
            )
        else:
            aliased = Alias(
                source=self.provides.with_component(DEFAULT_COMPONENT),
                cache=False,
                override=self.override,
                provides=DependencyKey(
                    component=component,
                    type_hint=self.provides.type_hint,
                ),
            )
            return aliased.as_factory(scope=self.scope, component=component)

    def __get__(self, instance: Any, owner: Any) -> ContextVariable:
        scope = self.scope or instance.scope
        return ContextVariable(
            scope=scope,
            provides=self.provides,
            override=self.override,
        )
