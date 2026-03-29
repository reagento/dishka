from collections.abc import Sequence
from functools import partial
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
from dishka.entities.scope import BaseScope
from dishka.registry import Registry


class StaticRegistry(Registry):
    def __init__(
            self,
            scope: BaseScope, *,
            has_fallback: bool,
            container_key: DependencyKey,
            is_root: bool,
    ) -> None:
        super().__init__(
            scope,
            has_fallback=has_fallback,
            container_key=container_key,
        )
        self.is_root = is_root

    def _is_static_allowed(self, factory: Factory) -> bool:
        if factory.type in (FactoryType.VALUE, FactoryType.ALIAS):
            return True
        if self.is_root and factory.type == FactoryType.CONTEXT:
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


def static_registry(registry: Registry, start_scope: BaseScope) -> StaticRegistry:
    new = StaticRegistry(
        registry.scope,
        has_fallback=False,
        container_key=registry.container_key,
        is_root=registry.scope <= start_scope,
    )
    new.factories = registry.factories
    return new


class ActivationContainer:
    def __init__(
            self,
            context: dict[Any, Any],
            registries: dict[BaseScope, Registry],
            container_key: DependencyKey,
            parent_container: "ActivationContainer | None",
    ):
        self._context = context
        self._registries = registries
        self._container_key = container_key.as_compilation_key()
        self._parent_container = parent_container

    @property
    def scope(self) -> BaseScope:
        return self._registry.scope

    def _get(self, dep: CompilationKey) -> Any:
        raise StaticEvaluationUnavailable

    def is_active(self, factory: Factory) -> bool:
        marker = factory.provides.as_compilation_key()
        registry = self._registries[factory.scope]
        compiled = registry.get_compiled_activation(marker)
        if not compiled:
            if self._has_nested(marker):
                print("has nested", marker, registry.scope)
                raise StaticEvaluationUnavailable
            if self._parent_container:  # FIXME
                return self._parent_container.is_active(factory)
            return False

        return bool(compiled(
            self._get,
            [],
            {},
            self._context,
            self,
            partial(self._has, scope=factory.scope),
        ))

    def _has(self, marker: CompilationKey, scope: BaseScope) -> bool:
        if marker == self._container_key:
            return True
        registry = self._registries[scope]
        compiled = registry.get_compiled_activation(marker)
        if not compiled:
            if self._parent_container:
                return self._parent_container._has(marker, scope)
            return False
        return bool(compiled(
            self._get,
            [],
            {},
            self._context,
            self,
            partial(self._has, scope=scope),
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
        scopes: Sequence[BaseScope],
        start_scope: BaseScope | None,
    ) -> None:
        if start_scope is None:
            start_scope = next(s for s in scopes if not s.skip)
        self.registries = {
            registry.scope: static_registry(registry, start_scope)
            for registry in registries
        }
        activation_container = ActivationContainer(
            registries=self.registries,
            container_key=container_key,
            context=context,
            parent_container=None,
        )
        self.activation_container = activation_container

    def _eval_activation(self, factory: Factory) -> None:
        try:
            active = self.activation_container.is_active(factory)
        except StaticEvaluationUnavailable:
            return
        if factory.when_override == factory.when_active:
            factory.when_override = BoolMarker(active)
        factory.when_active = BoolMarker(active)

    def evaluate_static(self) -> None:
        for registry in self.registries.values():
            for factory in list(registry.factories.values()):
                self._eval_activation(factory)
