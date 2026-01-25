from __future__ import annotations

from typing import TYPE_CHECKING

from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.key import DependencyKey
from dishka.entities.marker import (
    AndMarker,
    BaseMarker,
    BoolMarker,
    Marker,
    NotMarker,
    OrMarker,
)
from dishka.registry import Registry

if TYPE_CHECKING:
    from dishka.dependency_source.factory import Factory


class RegistryFilter:
    def __init__(
        self,
        activation_results: dict[DependencyKey, bool],
    ) -> None:
        self._activation_results = activation_results

    def _eval_simple_marker(
        self,
        marker: Marker,
        provides_key: DependencyKey | None,
    ) -> bool | None:
        key = DependencyKey(
            marker,
            provides_key.component if provides_key else DEFAULT_COMPONENT,
        )
        return self._activation_results.get(key)

    def _eval_not_marker(
        self,
        marker: NotMarker,
        provides_key: DependencyKey | None,
    ) -> bool | None:
        inner = self._is_marker_active(marker.marker, provides_key)
        return None if inner is None else not inner

    def _eval_or_marker(
        self,
        marker: OrMarker,
        provides_key: DependencyKey | None,
    ) -> bool | None:
        left = self._is_marker_active(marker.left, provides_key)
        right = self._is_marker_active(marker.right, provides_key)
        if left is True or right is True:
            return True
        if left is None or right is None:
            return None
        return False

    def _eval_and_marker(
        self,
        marker: AndMarker,
        provides_key: DependencyKey | None,
    ) -> bool | None:
        left = self._is_marker_active(marker.left, provides_key)
        right = self._is_marker_active(marker.right, provides_key)
        if left is False or right is False:
            return False
        if left is None or right is None:
            return None
        return True

    def _is_marker_active(
        self,
        marker: BaseMarker | None,
        provides_key: DependencyKey | None,
    ) -> bool | None:
        result: bool | None
        match marker:
            case None:
                result = True
            case BoolMarker():
                result = None if not marker.value else True
            case NotMarker():
                result = self._eval_not_marker(marker, provides_key)
            case OrMarker():
                result = self._eval_or_marker(marker, provides_key)
            case AndMarker():
                result = self._eval_and_marker(marker, provides_key)
            case Marker():
                result = self._eval_simple_marker(marker, provides_key)
            case _:
                result = None
        return result

    def _should_include_factory(self, factory: Factory) -> bool:
        if factory.when_active is None:
            return True

        result = self._is_marker_active(
            factory.when_active,
            factory.provides,
        )

        if result is None:
            return True
        return result

    def filter(
        self,
        registries: tuple[Registry, ...],
    ) -> tuple[Registry, ...]:
        if not self._activation_results:
            return registries

        filtered: list[Registry] = []

        for registry in registries:
            new_registry = Registry(
                registry.scope,
                has_fallback=registry.has_fallback,
            )

            for key, factory in registry.factories.items():
                if self._should_include_factory(factory):
                    new_registry.add_factory(factory, key)

            filtered.append(new_registry)

        return tuple(filtered)
