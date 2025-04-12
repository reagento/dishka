from typing import Any

from dishka.dependency_source import (
    CompositeDependencySource,
    ContextVariable,
    context_stub,
)
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from dishka.entities.type_alias_type import unwrap_type_alias


def from_context(
        provides: Any,
        *,
        scope: BaseScope | None = None,
        override: bool = False,
) -> CompositeDependencySource:
    composite = CompositeDependencySource(origin=context_stub)
    composite.dependency_sources.append(
        ContextVariable(
            scope=scope,
            override=override,
            provides=DependencyKey(
                type_hint=unwrap_type_alias(provides),
                component=DEFAULT_COMPONENT,
            ),
        ),
    )
    return composite
