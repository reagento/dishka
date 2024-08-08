from __future__ import annotations

from typing import Annotated, Any, NamedTuple, get_args, get_origin

from .component import DEFAULT_COMPONENT, Component


class FromComponent(NamedTuple):
    component: Component = DEFAULT_COMPONENT


class DependencyKey(NamedTuple):
    type_hint: Any
    component: Component | None

    def with_component(self, component: Component | None) -> DependencyKey:
        if self.component is not None:
            return self
        return DependencyKey(
            type_hint=self.type_hint,
            component=component,
        )

    def __str__(self) -> str:
        return f"({self.type_hint}, component={self.component!r})"


def hint_to_dependency_key(hint: Any) -> DependencyKey:
    if get_origin(hint) is not Annotated:
        return DependencyKey(hint, None)
    args = get_args(hint)
    from_component = next(
        (arg for arg in args if isinstance(arg, FromComponent)),
        None,
    )
    if from_component is None:
        return DependencyKey(args[0], None)
    return DependencyKey(args[0], from_component.component)


def hints_to_dependency_keys(hints: list[Any]) -> list[DependencyKey]:
    return [
        hint_to_dependency_key(type_hint)
        for type_hint in hints
    ]
