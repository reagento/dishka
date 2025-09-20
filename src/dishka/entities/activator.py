from collections.abc import Callable
from typing import Any, NamedTuple, TypeAlias

from dishka.entities.component import Component
from dishka.entities.key import DependencyKey


class ActivationCtx(NamedTuple):
    container_ctx: dict[Any, Any] | None
    container_key: DependencyKey
    registered_deps: list[DependencyKey]
    component: Component


ActivationFunc: TypeAlias = Callable[[ActivationCtx], bool]
