from collections.abc import Sequence

from dishka.dependency_source import Factory
from dishka.entities.key import DependencyKey
from .name import get_name


def render_suggestions_for_missing(
        requested_for: Factory,
        requested_key: DependencyKey,
        suggest_other_scopes: Sequence[Factory],
        suggest_other_components: Sequence[Factory],
):
    suggestion = ""
    if suggest_other_scopes:
        src_name = get_name(requested_for.source, include_module=False)
        scopes = " or ".join(
            str(factory.scope)
            for factory in suggest_other_scopes
        )
        suggestion += f"\n * Try changing scope of `{src_name}` to {scopes}."
    if suggest_other_components:
        dep_name = get_name(requested_key.type_hint, include_module=True)
        components_str = " or ".join(
            f"Annotated[{dep_name}, FromComponent({f.provides.component!r})]"
            for f in suggest_other_components
        )
        suggestion += f"\n * Try using {components_str}."
    return suggestion
