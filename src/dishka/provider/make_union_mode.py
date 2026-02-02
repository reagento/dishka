from typing import Any

from dishka.dependency_source import (
    CompositeDependencySource,
    FactoryUnionMode,
)
from dishka.entities.key import DependencyKey, hint_to_dependency_key
from dishka.entities.scope import BaseScope


def collect(
        source: Any,
        *,
        scope: BaseScope | None = None,
        cache: bool = True,
) -> CompositeDependencySource:
    src = CompositeDependencySource(source)
    key = hint_to_dependency_key(source)
    src.dependency_sources.append(FactoryUnionMode(
        source=key,
        collect=True,
        cache=cache,
        scope=scope,
        provides=DependencyKey(list[key.type_hint], key.component),
    ))
    return src
