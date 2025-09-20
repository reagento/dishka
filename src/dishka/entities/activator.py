from abc import abstractmethod
from collections.abc import Callable
from typing import Any, NamedTuple, Protocol, TypeAlias

from dishka.entities.component import Component
from dishka.entities.key import DependencyKey


class ActivationBuilder(Protocol):
    @abstractmethod
    def has_active(
        self,
        key: DependencyKey,
        request_stack: list[DependencyKey],
    ) -> bool:
        raise NotImplementedError


class ActivationCtx(NamedTuple):
    container_ctx: dict[Any, Any] | None
    container_key: DependencyKey
    key: DependencyKey
    registered_deps: list[DependencyKey]
    builder: ActivationBuilder
    request_stack: list[DependencyKey]


ActivationFunc: TypeAlias = Callable[[ActivationCtx], bool]


class Has:
    def __init__(
        self,
        cls: Any, *,
        component: Component | None = None,
    ) -> None:
        self.key = DependencyKey(cls, component=component)

    def __call__(self, ctx: ActivationCtx) -> bool:
        key = self.key.with_component(ctx.key.component)
        if key in ctx.request_stack:  # cycle
            return True
        return ctx.builder.has_active(key, ctx.request_stack)
