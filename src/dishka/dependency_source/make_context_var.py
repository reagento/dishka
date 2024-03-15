from typing import (
    Any,
)

from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .context_var import ContextVariable


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
