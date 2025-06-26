from __future__ import annotations

from typing import Annotated, Any, NamedTuple, get_args, get_origin

from .component import DEFAULT_COMPONENT, Component


class _FromComponent(NamedTuple):
    component: Component


def FromComponent(  # noqa: N802
    component: Component = DEFAULT_COMPONENT,
) -> _FromComponent:
    return _FromComponent(component)


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


def dependency_key_to_hint(key: DependencyKey) -> Any:
    if key.component is None:
        return key.type_hint
    return Annotated[key.type_hint, FromComponent(key.component)]


def hint_to_dependency_key(hint: Any) -> DependencyKey:
    if get_origin(hint) is not Annotated:
        return DependencyKey(hint, None)
    args = get_args(hint)
    from_component = next(
        (arg for arg in args if isinstance(arg, _FromComponent)),
        None,
    )
    if from_component is None:
        return DependencyKey(args[0], None)
    return DependencyKey(args[0], from_component.component)
