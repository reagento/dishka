from __future__ import annotations

from dishka.dependency_source.factory import Factory
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


class ProcessedFactoryFilter:
    def __init__(
        self,
        activation_results: dict[DependencyKey, bool],
    ) -> None:
        self._activation_results = activation_results

    def _eval_simple_marker(
        self,
        marker: Marker,
        component: str,
    ) -> bool | None:
        key = DependencyKey(marker, component)
        return self._activation_results.get(key)

    def _eval_not_marker(
        self,
        marker: NotMarker,
        component: str,
    ) -> bool | None:
        inner = self._is_marker_active(marker.marker, component)
        return None if inner is None else not inner

    def _eval_or_marker(
        self,
        marker: OrMarker,
        component: str,
    ) -> bool | None:
        left = self._is_marker_active(marker.left, component)
        right = self._is_marker_active(marker.right, component)
        if left is True or right is True:
            return True
        if left is None or right is None:
            return None
        return False

    def _eval_and_marker(
        self,
        marker: AndMarker,
        component: str,
    ) -> bool | None:
        left = self._is_marker_active(marker.left, component)
        right = self._is_marker_active(marker.right, component)
        if left is False or right is False:
            return False
        if left is None or right is None:
            return None
        return True

    def _is_marker_active(  # noqa: PLR0911
        self,
        marker: BaseMarker | None,
        component: str,
    ) -> bool | None:
        match marker:
            case None:
                return True
            case BoolMarker():
                return None if not marker.value else True
            case NotMarker():
                return self._eval_not_marker(marker, component)
            case OrMarker():
                return self._eval_or_marker(marker, component)
            case AndMarker():
                return self._eval_and_marker(marker, component)
            case Marker():
                return self._eval_simple_marker(marker, component)
            case _:
                return None

    def _should_include_factory(
        self,
        factory: Factory,
        component: str,
    ) -> bool:
        if factory.when_active is None:
            return True

        result = self._is_marker_active(factory.when_active, component)

        if result is None:
            return True  # Dynamic - keep
        return result  # True=keep, False=remove

    def filter(
        self,
        processed_factories: dict[DependencyKey, list[Factory]],
    ) -> dict[DependencyKey, list[Factory]]:
        if not self._activation_results:
            return processed_factories

        filtered: dict[DependencyKey, list[Factory]] = {}

        for key, factory_list in processed_factories.items():
            component = key.component or DEFAULT_COMPONENT
            kept = [
                f for f in factory_list
                if self._should_include_factory(f, component)
            ]
            if kept:
                filtered[key] = kept

        return filtered
