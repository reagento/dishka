from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from dishka.dependency_source.activator import Activator
from dishka.dependency_source.factory import Factory
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import Marker
from dishka.entities.scope import BaseScope
from dishka.factory_index import FactoryIndex


class ActivatorType(Enum):
    STATIC = auto()
    DYNAMIC = auto()


@dataclass(frozen=True, slots=True)
class ClassifiedActivator:
    key: DependencyKey
    activator: Activator
    type: ActivatorType
    dependencies: frozenset[DependencyKey]


class ActivatorClassifier:
    def __init__(
        self,
        factory_index: FactoryIndex,
        activators: dict[DependencyKey, Activator],
        root_scope: BaseScope,
    ) -> None:
        self._factory_index = factory_index
        self._activators = activators
        self._root_scope = root_scope

    def _is_async_factory(self, factory: Factory) -> bool:
        return factory.type in (
            FactoryType.ASYNC_FACTORY,
            FactoryType.ASYNC_GENERATOR,
        )

    def _is_marker_dependency(
        self,
        activator: Activator,
        dep: DependencyKey,
    ) -> bool:
        return (
            dep.type_hint is activator.marker_type
            or dep.type_hint is Marker
        )

    def _get_activator_dependencies(
        self,
        activator: Activator,
    ) -> frozenset[DependencyKey]:
        factory = activator.factory
        all_deps = list(factory.dependencies) + list(
            factory.kw_dependencies.values(),
        )
        return frozenset(
            dep for dep in all_deps
            if dep in self._activators
            and not self._is_marker_dependency(activator, dep)
        )

    def _get_all_dependencies(
        self,
        activator: Activator,
    ) -> list[DependencyKey]:
        factory = activator.factory
        all_deps = list(factory.dependencies) + list(
            factory.kw_dependencies.values(),
        )
        return [
            dep for dep in all_deps
            if not self._is_marker_dependency(activator, dep)
        ]

    def _is_root_context_dep(self, dep: DependencyKey) -> bool:
        return dep in self._factory_index.context_keys_at_root

    def _is_registered(self, dep: DependencyKey) -> bool:
        return dep in self._factory_index or dep in self._activators

    def _topological_sort(
        self,
        activator_deps: dict[DependencyKey, frozenset[DependencyKey]],
    ) -> list[DependencyKey]:
        result: list[DependencyKey] = []
        visited: set[DependencyKey] = set()

        def visit(key: DependencyKey) -> None:
            if key in visited:
                return
            for dep in activator_deps.get(key, frozenset()):
                if dep in activator_deps:
                    visit(dep)
            visited.add(key)
            result.append(key)

        for key in activator_deps:
            visit(key)

        return result

    def classify(self) -> dict[DependencyKey, ClassifiedActivator]:
        activator_deps: dict[DependencyKey, frozenset[DependencyKey]] = {}
        for key, activator in self._activators.items():
            activator_deps[key] = self._get_activator_dependencies(activator)

        eval_order = self._topological_sort(activator_deps)

        classification: dict[DependencyKey, ClassifiedActivator] = {}

        for key in eval_order:
            activator = self._activators[key]
            activator_type = self._classify_single(
                activator,
                activator_deps[key],
                classification,
            )
            classification[key] = ClassifiedActivator(
                key=key,
                activator=activator,
                type=activator_type,
                dependencies=activator_deps[key],
            )

        return classification

    def _classify_single(
        self,
        activator: Activator,
        activator_dependencies: frozenset[DependencyKey],
        already_classified: dict[DependencyKey, ClassifiedActivator],
    ) -> ActivatorType:
        factory = activator.factory

        if self._is_async_factory(factory):
            return ActivatorType.DYNAMIC

        all_deps = self._get_all_dependencies(activator)

        if not all_deps:
            return ActivatorType.STATIC

        for dep in activator_dependencies:
            classified = already_classified.get(dep)
            if classified and classified.type == ActivatorType.DYNAMIC:
                return ActivatorType.DYNAMIC

        non_activator_deps = [
            dep for dep in all_deps if dep not in self._activators
        ]

        for dep in non_activator_deps:
            if self._is_root_context_dep(dep):
                continue
            if not self._is_registered(dep):
                continue
            return ActivatorType.DYNAMIC

        return ActivatorType.STATIC
