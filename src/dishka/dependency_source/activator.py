from inspect import iscoroutinefunction
from typing import Any

from dishka.entities.component import Component
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey, const_dependency_key
from dishka.entities.marker import Marker
from dishka.entities.scope import BaseScope
from .factory import Factory


class Activator:
    __slots__ = ("factory", "marker", "marker_type")

    def __init__(
        self,
        factory: Factory,
        marker: Marker | None,
        marker_type: type[Marker] | None,
    ) -> None:
        self.factory = factory
        self.marker = marker
        self.marker_type = marker_type

    def __get__(self, instance: Any, owner: Any) -> "Activator":
        return Activator(
            factory=self.factory.__get__(instance, owner),
            marker=self.marker,
            marker_type=self.marker_type,
        )

    def _replace_dep(
        self,
        dependency: DependencyKey,
        marker: Marker,
    ) -> DependencyKey:
        if (
            dependency.type_hint is self.marker_type or
            dependency.type_hint is Marker or
            dependency.type_hint is Marker
        ):
            return const_dependency_key(marker)
        return dependency

    def with_component(self, component: Component) -> "Activator":
        return Activator(
            factory=self.factory.with_component(component),
            marker=self.marker,
            marker_type=self.marker_type,
        )

    def as_factory(
        self,
        scope: BaseScope | None,
        component: Component | None,
        marker_key: DependencyKey,
    ) -> Factory:
        factory = self.factory.with_component(component)
        marker = marker_key.type_hint
        return Factory(
            scope=scope,
            source=factory.source,
            provides=marker_key,
            is_to_bind=factory.is_to_bind,
            dependencies=[
                self._replace_dep(d, marker)
                for d in factory.dependencies
            ],
            kw_dependencies={
                name: self._replace_dep(d, marker)
                for name, d in factory.kw_dependencies.items()
            },
            type_=factory.type,
            cache=factory.cache,
            when_override=factory.when_override,
            when_active=factory.when_active,
            when_component=factory.when_component,
            when_dependencies=factory.when_dependencies,
        )

    def is_static_evaluated(self) -> bool:
        """
        Check if this activator can be statically evaluated.

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
