from typing import (
    Any,
)

from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .composite import CompositeDependencySource
from .context_var import ContextVariable, context_stub


def from_context(
        *, provides: Any, scope: BaseScope | None = None,
) -> CompositeDependencySource:
    composite = CompositeDependencySource(origin=context_stub)
    composite.dependency_sources.append(ContextVariable(
        provides=DependencyKey(
            type_hint=provides,
            component=DEFAULT_COMPONENT,
        ),
        scope=scope,
    ))
    return composite
