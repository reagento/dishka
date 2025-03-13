from collections.abc import Sequence

from dishka.entities.factory_type import FactoryData
from dishka.entities.key import DependencyKey
from .name import get_name


def render_suggestions_for_missing(
        requested_for: FactoryData | None,
        requested_key: DependencyKey,
        suggest_other_scopes: Sequence[FactoryData],
        suggest_other_components: Sequence[FactoryData],
) -> str:
    suggestion = ""
    if suggest_other_scopes:
        scopes = " or ".join(
            str(factory.scope)
            for factory in suggest_other_scopes
        )
        if requested_for:
            srcname = get_name(requested_for.source, include_module=False)
            suggestion += f"\n * Try changing scope of `{srcname}` to {scopes}"
        else:
            suggestion += f"\n * Check if you forgot enter {scopes}"

    if suggest_other_components:
        dep_name = get_name(requested_key.type_hint, include_module=True)
        components_str = " or ".join(
            f"Annotated[{dep_name}, FromComponent({f.provides.component!r})]"
            for f in suggest_other_components
        )
        suggestion += f"\n * Try using {components_str}"
    return suggestion
