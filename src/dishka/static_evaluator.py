from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dishka.activator_classifier import (
    ActivatorClassifier,
    ActivatorType,
    ClassifiedActivator,
)
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
from dishka.entities.scope import BaseScope
from dishka.exceptions import NoContextValueError
from dishka.registry_filter import RegistryFilter

if TYPE_CHECKING:
    from dishka.dependency_source.activator import Activator
    from dishka.dependency_source.factory import Factory
    from dishka.registry import Registry


def _determine_root_scope(
    registries: tuple[Registry, ...],
    start_scope: BaseScope | None,
) -> BaseScope:
    if start_scope is not None:
        return start_scope
    for registry in registries:
        if not registry.scope.skip:
            return registry.scope
    return registries[0].scope


def apply_static_evaluation(
    registries: tuple[Registry, ...],
    activators: dict[DependencyKey, Activator],
    context: dict[Any, Any] | None,
    start_scope: BaseScope | None = None,
) -> tuple[Registry, ...]:
    if not activators:
        return registries

    root_scope = _determine_root_scope(registries, start_scope)
    classifier = ActivatorClassifier(registries, activators, root_scope)
    classification = classifier.classify()

    evaluator = StaticActivatorEvaluator(
        classification,
        context or {},
        registries,
    )
    activation_results = evaluator.evaluate()

    if not activation_results:
        return registries

    registry_filter = RegistryFilter(activation_results)
    return registry_filter.filter(registries)


class StaticActivatorEvaluator:
    def __init__(
        self,
        classification: dict[DependencyKey, ClassifiedActivator],
        context: dict[Any, Any],
        registries: tuple[Registry, ...],
    ) -> None:
        self._classification = classification
        self._context = context
        self._registries = registries
        self._context_by_type: dict[type, Any] = {
            type(v): v for v in context.values()
        }
        for k, v in context.items():
            if isinstance(k, type):
                self._context_by_type[k] = v
        self._registered_keys = self._build_registered_keys()

    def _build_registered_keys(self) -> set[DependencyKey]:
        keys: set[DependencyKey] = set()
        for registry in self._registries:
            keys.update(registry.factories.keys())
        return keys

    def _evaluate_has(self, marker: Has) -> bool:
        # Search across all registered keys for this type (any component)
        matching_key = None
        for key in self._registered_keys:
            if key.type_hint == marker.value:
                matching_key = key
                break

        if matching_key is None:
            return False

        factory = self._get_factory(matching_key)
        if factory is None:
            return False
        if factory.type == FactoryType.CONTEXT:
            return marker.value in self._context_by_type
        return True

    def _get_factory(self, key: DependencyKey) -> Factory | None:
        for registry in self._registries:
            if key in registry.factories:
                return registry.factories[key]
        return None

    def _collect_has_markers_from_when(
        self,
        marker: BaseMarker | None,
        component: str,
    ) -> dict[DependencyKey, Has]:
        """Collect Has markers from when expression for static evaluation.

        Note: HasContext markers are intentionally excluded - they are
        evaluated at runtime to preserve from_context factory behavior.
        """
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
        for registry in self._registries:
            for key, factory in registry.factories.items():
                component = key.component or DEFAULT_COMPONENT
                markers = self._collect_has_markers_from_when(
                    factory.when_active,
                    component,
                )
                all_markers.update(markers)
        return all_markers

    def _get_static_activators(
        self,
    ) -> dict[DependencyKey, ClassifiedActivator]:
        return {
            key: classified
            for key, classified in self._classification.items()
            if classified.type == ActivatorType.STATIC
        }

    def _topological_sort(
        self,
        static_activators: dict[DependencyKey, ClassifiedActivator],
    ) -> list[DependencyKey]:
        result: list[DependencyKey] = []
        visited: set[DependencyKey] = set()

        def visit(key: DependencyKey) -> None:
            if key in visited:
                return
            classified = static_activators.get(key)
            if classified:
                for dep in classified.dependencies:
                    if dep in static_activators:
                        visit(dep)
            visited.add(key)
            result.append(key)

        for key in static_activators:
            visit(key)

        return result

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

        static_activators = self._get_static_activators()
        if static_activators:
            eval_order = self._topological_sort(static_activators)
            for key in eval_order:
                classified = static_activators[key]
                result = self._evaluate_activator(
                    classified.activator,
                    results,
                )
                results[key] = result

        has_markers = self._collect_all_has_markers()
        for key, marker in has_markers.items():
            results[key] = self._evaluate_has(marker)

        return results
