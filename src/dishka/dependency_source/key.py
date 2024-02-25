from dataclasses import dataclass
from typing import Any

from ..component import Component


@dataclass(frozen=True)
class DependencyKey:
    type_hint: Any
    component: Component | None = None

    def with_component(self, component: Component) -> "DependencyKey":
        if self.component is not None:
            return self
        return DependencyKey(
            type_hint=self.type_hint,
            component=component,
        )
