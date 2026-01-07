from inspect import iscoroutinefunction
from typing import Any

from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from dishka.entities.marker import Marker
from dishka.entities.scope import BaseScope
from ..entities.factory_type import FactoryType
from .factory import Factory


class Activator:
    __slots__ = ("factory", "markers")

    def __init__(
        self,
        factory: Factory,
        markers: tuple[Marker, ...] = (),
    ) -> None:
        self.factory = factory
        self.markers = markers

    def __get__(self, instance: Any, owner: Any) -> "Activator":
        return Activator(
            factory=self.factory.__get__(instance, owner),
            markers=self.markers,
        )

    def as_factory(
        self,
        scope: BaseScope | None,
        component: Component | None,
        marker: Marker,
    ) -> Factory:
        factory = self.factory.with_component(component)
        return Factory(
            scope=scope,
            source=factory.source,
            provides=DependencyKey(type_hint=marker, component=component),
            is_to_bind=factory.is_to_bind,
            dependencies=factory.dependencies,
            kw_dependencies=factory.kw_dependencies,
            type_=factory.type,
            cache=factory.cache,
            override=factory.override,
            when=factory.when,
        )

    def is_static_evaluated(self) -> bool:
        """Check if this activator can be statically evaluated.
        
        Static rules (activator is static if):
        - Must be a regular (non-async) factory
        - No dependencies OR
        - Only depends on context variables with root scope OR
        - Only depends on objects not registered in graph OR
        - Only depends on result of other static activators
        
        Dynamic rules (activator is dynamic if):
        - Async functions are always dynamic
        - Functions depending on graph objects that are not static
        
        Note: Full implementation requires access to the entire graph
        during compilation. This is a simplified version.
        """
        # Async factories are always dynamic
        if self.factory.type is FactoryType.ASYNC_FACTORY:
            return False
        if self.factory.type is FactoryType.ASYNC_GENERATOR:
            return False
        if iscoroutinefunction(self.factory.source):
            return False

        # Must be a regular factory
        if self.factory.type is not FactoryType.FACTORY:
            return False

        # No dependencies = static
        if not self.factory.dependencies and not self.factory.kw_dependencies:
            return True

        # TODO: Full static detection requires access to:
        # - Root context scope information
        # - Graph of other activators
        # - Whether dependencies are registered or not
        # For now, return False for any dependencies
        return False

    def provides_for_marker(self, marker: Marker | Any) -> bool:
        """Check if this activation provides a result for the given marker."""
        if not isinstance(marker, Marker):
            return False

        for m in self.markers:
            if isinstance(m, type) and isinstance(marker, m):
                # Generic marker type match
                return True
            elif m == marker:
                # Exact marker match
                return True
        return False
