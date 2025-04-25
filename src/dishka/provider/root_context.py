from typing import Any

from dishka.entities.scope import BaseScope
from .base_provider import BaseProvider
from .provider import Provider


def make_root_context_provider(
        context: dict[Any, Any] | None,
        scopes: type[BaseScope],
) -> BaseProvider:
    p = Provider()
    if not context:
        return p
    root_scope = next(iter(scopes))
    for key in context:
        p.from_context(provides=key, scope=root_scope)
    return p
