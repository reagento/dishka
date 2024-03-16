from typing import Any

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .alias import Alias
from .factory import Factory, FactoryType


def context_stub() -> Any:
    raise NotImplementedError


class ContextVariable:
    __slots__ = ("provides", "scope")

    def __init__(
            self, *,
            provides: DependencyKey,
            scope: BaseScope,
    ) -> None:
        self.provides = provides
        self.scope = scope

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
                type_=FactoryType.CONTEXT,
                cache=False,
            )
        else:
            aliased = Alias(
                source=self.provides.with_component(DEFAULT_COMPONENT),
                provides=DependencyKey(self.provides.type_hint,
                                       component=component),
                cache=False,
            )
            return aliased.as_factory(scope=self.scope, component=component)

    def __get__(self, instance, owner):
        scope = self.scope or instance.scope
        return ContextVariable(
            scope=scope,
            provides=self.provides,
        )
