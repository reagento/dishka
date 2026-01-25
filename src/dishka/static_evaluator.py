from __future__ import annotations

from typing import Any

from dishka.activator_classifier import (
    ActivatorType,
    ClassifiedActivator,
)
from dishka.dependency_source.activator import Activator
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import (
    AndMarker,
    BaseMarker,
    Has,
    NotMarker,
    OrMarker,
)
from dishka.exceptions import NoContextValueError
from dishka.factory_index import FactoryIndex


class StaticActivatorEvaluator:
    def __init__(
        self,
        classification: dict[DependencyKey, ClassifiedActivator],
        context: dict[Any, Any],
        factory_index: FactoryIndex,
    ) -> None:
        self._classification = classification
        self._context = context
        self._factory_index = factory_index
        self._context_by_type: dict[type, Any] = {
            type(v): v for v in context.values()
        }
        for k, v in context.items():
            if isinstance(k, type):
                self._context_by_type[k] = v

    def _evaluate_has(self, marker: Has) -> bool:
        matching_key = None
        for key in self._factory_index.factories_by_key:
            if key.type_hint == marker.value:
                matching_key = key
                break

        if matching_key is None:
            return False

        factory = self._factory_index.get(matching_key)
        if factory is None:
            return False
        if factory.type == FactoryType.CONTEXT:
            return marker.value in self._context_by_type
        return True

    def _collect_has_markers_from_when(
        self,
        marker: BaseMarker | None,
        component: str,
    ) -> dict[DependencyKey, Has]:
        result: dict[DependencyKey, Has] = {}
        if marker is None:
            return result
        if isinstance(marker, Has):
            key = DependencyKey(marker, component)
            result[key] = marker
        elif isinstance(marker, NotMarker):
            result.update(
                self._collect_has_markers_from_when(marker.marker, component),
            )
        elif isinstance(marker, (OrMarker, AndMarker)):
            result.update(
                self._collect_has_markers_from_when(marker.left, component),
            )
            result.update(
                self._collect_has_markers_from_when(marker.right, component),
            )
        return result

    def _collect_all_has_markers(self) -> dict[DependencyKey, Has]:
        all_markers: dict[DependencyKey, Has] = {}
        for key, factory in self._factory_index.factories_by_key.items():
            component = key.component or DEFAULT_COMPONENT
            markers = self._collect_has_markers_from_when(
                factory.when_active,
                component,
            )
            all_markers.update(markers)
        return all_markers

    def _resolve_dependency(
        self,
        dep: DependencyKey,
        evaluated_results: dict[DependencyKey, bool],
    ) -> Any:
        if dep in evaluated_results:
            return evaluated_results[dep]

        type_hint = dep.type_hint
        if type_hint in self._context_by_type:
            return self._context_by_type[type_hint]

        for ctx_value in self._context.values():
            if isinstance(ctx_value, type_hint):
                return ctx_value

        raise NoContextValueError(type_hint)

    def _evaluate_activator(
        self,
        activator: Activator,
        evaluated_results: dict[DependencyKey, bool],
    ) -> bool:
        factory = activator.factory

        try:
            args = []
            for dep in factory.dependencies:
                args.append(self._resolve_dependency(dep, evaluated_results))

            kwargs = {}
            for name, dep in factory.kw_dependencies.items():
                kwargs[name] = self._resolve_dependency(dep, evaluated_results)
        except NoContextValueError:
            return False

        source = factory.source
        if factory.is_to_bind and args:
            result = source(args[0], *args[1:], **kwargs)
        else:
            result = source(*args, **kwargs)

        return bool(result)

    def evaluate(self) -> dict[DependencyKey, bool]:
        results: dict[DependencyKey, bool] = {}

        for key, classified in self._classification.items():
            if classified.type == ActivatorType.STATIC:
                result = self._evaluate_activator(
                    classified.activator,
                    results,
                )
                results[key] = result

        has_markers = self._collect_all_has_markers()
        for key, marker in has_markers.items():
            results[key] = self._evaluate_has(marker)

        return results
