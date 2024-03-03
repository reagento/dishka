from typing import (
    Any,
)

from dishka.entities.component import DEFAULT_COMPONENT, Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .alias import alias
from .factory import Factory, FactoryType


def _context_stub() -> Any:
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
                source=_context_stub,
                provides=self.provides,
                is_to_bind=False,
                dependencies=[],
                type_=FactoryType.CONTEXT,
                cache=False,
            )
        else:
            aliased = alias(
                source=self.provides.type_hint,
                component=DEFAULT_COMPONENT,
            )
            return aliased.as_factory(scope=self.scope, component=component)

    def __get__(self, instance, owner):
        scope = self.scope or instance.scope
        return ContextVariable(
            scope=scope,
            provides=self.provides,
        )


def from_context(
        *, provides: Any, scope: BaseScope | None = None,
) -> ContextVariable:
    return ContextVariable(
        provides=DependencyKey(
            type_hint=provides,
            component=DEFAULT_COMPONENT,
        ),
        scope=scope,
    )
