import itertools
from collections.abc import Sequence
from enum import Enum

from dishka.dependency_source import Factory
from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from dishka.entities.marker import (
    AndMarker,
    BaseMarker,
    BoolMarker,
    Has,
    Marker,
    NotMarker,
    OrMarker,
)
from dishka.exceptions import (
    CycleDependenciesError,
    GraphMissingFactoryError,
    InvalidSubfactoryScopeError,
    NoFactoryError,
)
from dishka.registry import Registry


class MarkerValue(Enum):
    TRUE = True
    FALSE = False
    UNKNOWN = None


class GraphValidator:
    def __init__(self, registries: Sequence[Registry]) -> None:
        self.registries = registries
        self.path: dict[DependencyKey, Factory] = {}
        self.valid_keys: dict[DependencyKey, bool] = {}

    def _get_factory(
        self,
        key: DependencyKey,
        registry_index: int,
    ) -> Factory | None:
        for index in range(registry_index + 1):
            factory = self.registries[index].get_factory(key)
            if factory is not None:
                return factory
        return None

    def _has_reachable_factory(
        self,
        key: DependencyKey,
        registry_index: int,
    ) -> bool:
        return self._get_factory(key, registry_index) is not None

    def _marker_component(self, component: Component | None) -> Component:
        if component is None:
            raise TypeError
        return component

    def _invert_marker_value(self, value: MarkerValue) -> MarkerValue:
        if value is MarkerValue.TRUE:
            return MarkerValue.FALSE
        if value is MarkerValue.FALSE:
            return MarkerValue.TRUE
        return MarkerValue.UNKNOWN

    def _and_marker_values(
        self,
        left: MarkerValue,
        right: MarkerValue,
    ) -> MarkerValue:
        if MarkerValue.FALSE in (left, right):
            return MarkerValue.FALSE
        if MarkerValue.TRUE == left == right:
            return MarkerValue.TRUE
        return MarkerValue.UNKNOWN

    def _or_marker_values(
        self,
        left: MarkerValue,
        right: MarkerValue,
    ) -> MarkerValue:
        if MarkerValue.TRUE in (left, right):
            return MarkerValue.TRUE
        if MarkerValue.FALSE == left == right:
            return MarkerValue.FALSE
        return MarkerValue.UNKNOWN

    def _eval_marker(
        self,
        marker: BaseMarker | None,
        component: Component | None,
        registry_index: int,
    ) -> MarkerValue:
        result = MarkerValue.UNKNOWN
        match marker:
            case None | BoolMarker(True):
                result = MarkerValue.TRUE
            case BoolMarker(False):
                result = MarkerValue.FALSE
            case AndMarker():
                result = self._and_marker_values(
                    self._eval_marker(marker.left, component, registry_index),
                    self._eval_marker(marker.right, component, registry_index),
                )
            case OrMarker():
                result = self._or_marker_values(
                    self._eval_marker(marker.left, component, registry_index),
                    self._eval_marker(marker.right, component, registry_index),
                )
            case NotMarker():
                result = self._invert_marker_value(
                    self._eval_marker(
                        marker.marker,
                        component,
                        registry_index,
                    ),
                )
            case Has():
                key = DependencyKey(
                    marker.value,
                    self._marker_component(component),
                )
                if self._has_reachable_factory(key, registry_index):
                    result = MarkerValue.UNKNOWN
                else:
                    result = MarkerValue.FALSE
            case Marker():
                result = MarkerValue.UNKNOWN
            case _:
                result = MarkerValue.UNKNOWN
        return result

    def _validate_key(
        self,
        key: DependencyKey,
        registry_index: int,
    ) -> None:
        if key in self.valid_keys:
            return
        if key.is_const():
            return
        if key.type_hint is DependencyKey:
            return
        if key in self.path:
            keys = list(self.path)
            factories = list(self.path.values())[keys.index(key):]
            raise CycleDependenciesError(factories)

        suggest_abstract_factories = []
        suggest_concrete_factories = []
        for index in range(registry_index + 1):
            registry = self.registries[index]
            factory = registry.get_factory(key)
            if factory:
                self._validate_factory(factory, registry_index)
                return

            abstract_factories = registry.get_more_abstract_factories(key)
            concrete_factories = registry.get_more_concrete_factories(key)
            suggest_abstract_factories.extend(abstract_factories)
            suggest_concrete_factories.extend(concrete_factories)

        raise NoFactoryError(
            requested=key,
            suggest_abstract_factories=suggest_abstract_factories,
            suggest_concrete_factories=suggest_concrete_factories,
        )

    def _validate_factory(
            self, factory: Factory, registry_index: int,
    ) -> None:
        self.path[factory.provides] = factory
        if (
            factory.provides in factory.kw_dependencies.values() or
            factory.provides in factory.dependencies
        ):
            raise CycleDependenciesError([factory])

        try:
            when_active = self._eval_marker(
                factory.when_active,
                factory.when_component,
                registry_index,
            )
            if when_active is not MarkerValue.FALSE:
                for dep in itertools.chain(
                    factory.dependencies,
                    factory.kw_dependencies.values(),
                ):
                    # ignore TypeVar and const parameters
                    if not dep.is_type_var() and not dep.is_const():
                        self._validate_key(dep, registry_index)
        except NoFactoryError as e:
            e.add_path(factory)
            raise
        finally:
            self.path.pop(factory.provides)

        if factory.scope is None:
            raise ValueError  # should be checked in builder
        for subfactory in factory.when_dependencies:
            if subfactory.scope is None:
                raise ValueError  # should be checked in builder
            if subfactory.scope > factory.scope:
                raise InvalidSubfactoryScopeError(factory, subfactory)

        self.valid_keys[factory.provides] = True

    def validate(self) -> None:
        for registry_index, registry in enumerate(self.registries):
            factories = tuple(registry.factories.values())
            for factory in factories:
                self.path = {}
                try:
                    self._validate_factory(factory, registry_index)
                except NoFactoryError as e:
                    raise GraphMissingFactoryError(
                        e.requested,
                        e.path,
                        self._find_other_scope(e.requested),
                        self._find_other_component(e.requested),
                        e.suggest_abstract_factories,
                        e.suggest_concrete_factories,
                    ) from None
                except CycleDependenciesError as e:
                    raise e from None

    def _find_other_scope(self, key: DependencyKey) -> list[Factory]:
        found = []
        for registry in self.registries:
            for factory_key, factory in registry.factories.items():
                if factory_key == key:
                    found.append(factory)
        return found

    def _find_other_component(self, key: DependencyKey) -> list[Factory]:
        found = []
        for registry in self.registries:
            for factory_key, factory in registry.factories.items():
                if factory_key.type_hint != key.type_hint:
                    continue
                if factory_key.component == key.component:
                    continue
                found.append(factory)
        return found
