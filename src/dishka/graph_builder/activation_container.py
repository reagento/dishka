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
from dishka.registry import Registry


class StaticRegistry(Registry):
    def _compile_factory(self, factory: Factory) -> CompiledFactory:
        if factory.type not in (FactoryType.VALUE, FactoryType.CONTEXT, FactoryType.ALIAS):
            raise StaticEvaluationUnavailable
        return super()._compile_factory(factory)

    def _compile_factory_async(self, factory: Factory) -> CompiledFactory:
        if factory.type not in (FactoryType.VALUE, FactoryType.CONTEXT, FactoryType.ALIAS):
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
