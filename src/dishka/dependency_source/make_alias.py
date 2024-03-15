from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from .alias import Alias


def alias(
        *,
        source: type,
        provides: type | None = None,
        cache: bool = True,
        component: Component | None = None,
) -> Alias:
    if component is provides is None:
        raise ValueError("Either component or provides must be set in alias")
    if provides is None:
        provides = source
    return Alias(
        source=DependencyKey(
            type_hint=source,
            component=component,
        ),
        provides=DependencyKey(provides, None),
        cache=cache,
    )
