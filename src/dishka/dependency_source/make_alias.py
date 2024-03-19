from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from .alias import Alias
from .composite import CompositeDependencySource, ensure_composite
from .unpack_provides import unpack_alias


def alias(
        *,
        source: type,
        provides: type | None = None,
        cache: bool = True,
        component: Component | None = None,
) -> CompositeDependencySource:
    if component is provides is None:
        raise ValueError("Either component or provides must be set in alias")
    if provides is None:
        provides = source

    composite = ensure_composite(source)
    alias = Alias(
        source=DependencyKey(
            type_hint=source,
            component=component,
        ),
        provides=DependencyKey(provides, None),
        cache=cache,
    )
    composite.dependency_sources.extend(unpack_alias(alias))
    return composite
