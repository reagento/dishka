from collections.abc import Sequence
from typing import Any

from dishka.container_objects import CompiledFactory
from dishka.dependency_source import Factory
from dishka.dependency_source.activator import StaticEvaluationUnavailable
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import (
    CompilationKey,
    DependencyKey,
    compilation_to_dependency_key,
)
from dishka.entities.marker import BoolMarker, Marker
from dishka.registry import Registry


class StaticRegistry(Registry):
    def _is_static_allowed(self, factory: Factory) -> bool:
        if factory.type in (FactoryType.VALUE, FactoryType.ALIAS, FactoryType.CONTEXT):
            return True
        if isinstance(factory.provides.type_hint, Marker) and factory.type is FactoryType.FACTORY:
            return True
        return False

    def _compile_factory(self, factory: Factory) -> CompiledFactory:
        if not self._is_static_allowed(factory):
            raise StaticEvaluationUnavailable
        return super()._compile_factory(factory)

    def _compile_factory_async(self, factory: Factory) -> CompiledFactory:
        if not self._is_static_allowed(factory):
            raise StaticEvaluationUnavailable
        return super()._compile_factory_async(factory)


def static_registry(registry: Registry) -> StaticRegistry:
    new = StaticRegistry(
        registry.scope,
        has_fallback=False,
        container_key=registry.container_key,
        child_registry=registry.child_registry,
    )
    new.factories = registry.factories
    return new


class ActivationContainer:
    def __init__(self, context: dict[Any, Any], registry: Registry, container_key: DependencyKey):
        self._context = context
        self._registry = registry
        self._container_key = container_key.as_compilation_key()

    def _get(self, dep: CompilationKey) -> Any:
        raise StaticEvaluationUnavailable

    def is_active(self, factory: Factory) -> bool:
        marker = factory.provides.as_compilation_key()
        compiled = self._registry.get_compiled_activation(marker)
        if not compiled:
            if self._has_nested(marker):
                raise StaticEvaluationUnavailable
            return False

        return bool(compiled(
            self._get,
            [],
            {},
            self._context,
            self,
            self._has,
        ))

    def _has(self, marker: CompilationKey) -> bool:
        if marker == self._container_key:
            return True
        compiled = self._registry.get_compiled_activation(marker)
        if not compiled:
            if self._has_nested(marker):
                raise StaticEvaluationUnavailable
            return False
        return bool(compiled(
            self._get_unlocked,
            self._exits,
            self._cache,
            self._context,
            self,
            self._has,
        ))

    def _has_nested(self, key: CompilationKey) -> bool:
        registry = self._registry
        while registry := registry.child_registry:
            factory = registry.get_factory(compilation_to_dependency_key(key))
            if factory is not None:
                return True
        return False


class StaticEvaluator:
    def __init__(
        self,
        registries: Sequence[Registry],
        context: dict[Any, Any],
        container_key: DependencyKey,
    ) -> None:
        self.registries = registries
        self.activation_container = ActivationContainer(
            registry=static_registry(registries[0]),
            container_key=container_key,
            context=context,
        )

    def _eval_activation(self, factory: Factory) -> None:
        try:
            active = self.activation_container.is_active(factory)
        except StaticEvaluationUnavailable:
            return
        if factory.when_override == factory.when_active:
            factory.when_override = BoolMarker(active)
        factory.when_active = BoolMarker(active)


    def evaluate_static(self) -> None:
        for registry in self.registries:
            for factory in list(registry.factories.values()):
                self._eval_activation(factory)
