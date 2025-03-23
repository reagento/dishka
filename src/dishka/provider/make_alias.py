from typing import Any

from dishka.dependency_source import (
    Alias,
    CompositeDependencySource,
    ensure_composite,
)
from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from .unpack_provides import unpack_alias


def alias(
        source: Any,
        *,
        provides: Any | None = None,
        cache: bool = True,
        component: Component | None = None,
        override: bool = False,
) -> CompositeDependencySource:
    if component is provides is None:
        raise ValueError(  # noqa: TRY003
            "Either component or provides must be set in alias",
        )
    if provides is None:
        provides = source

    composite = ensure_composite(source)
    alias_instance = Alias(
        source=DependencyKey(
            type_hint=source,
            component=component,
        ),
        provides=DependencyKey(provides, None),
        cache=cache,
        override=override,
    )
    composite.dependency_sources.extend(unpack_alias(alias_instance))
    return composite
