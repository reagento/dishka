from collections.abc import Sequence
from functools import partial
from logging import getLogger
from typing import Any

from dishka.container_objects import CompiledFactory
from dishka.dependency_source import Factory
from dishka.dependency_source.activator import StaticEvaluationUnavailable
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import (
    CompilationKey,
    DependencyKey,
)
from dishka.entities.marker import BoolMarker, Marker
from dishka.entities.scope import BaseScope
from dishka.exception_base import DishkaError
from dishka.registry import Registry
from dishka.text_rendering.name import get_source_name

logger = getLogger(__name__)


class StaticRegistry(Registry):
    def __init__(
            self,
            scope: BaseScope,
            *,
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
        if factory.type in (
            FactoryType.VALUE,
            FactoryType.ALIAS,
            FactoryType.SELECTOR,
        ):
            return True
        if (
            factory.allow_static_evaluation
            and factory.type is FactoryType.FACTORY
        ):
            return True
        if self.is_root and factory.type == FactoryType.CONTEXT:
            return True
        if (
            isinstance(factory.provides.type_hint, Marker)
            and factory.type is FactoryType.FACTORY
        ):
            return True
        return False

    def _compile_factory(self, factory: Factory) -> CompiledFactory:
        if not self._is_static_allowed(factory):
            raise StaticEvaluationUnavailable(factory)
        return super()._compile_factory(factory)

    def _compile_factory_async(self, factory: Factory) -> CompiledFactory:
        if not self._is_static_allowed(factory):
            raise StaticEvaluationUnavailable(factory)
        return super()._compile_factory_async(factory)


def static_registry(
    registry: Registry,
    start_scope: BaseScope,
) -> StaticRegistry:
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
    ) -> None:
        self._context = context
        self._registries = registries
        self._container_key = container_key.as_compilation_key()
        self._cache_by_scope: dict[BaseScope, dict[Any, object]] = {
            scope: {} for scope in registries
        }

        self._parent_scopes: dict[BaseScope, BaseScope | None] = {}
        prev_scope = None
        for scope in registries:
            self._parent_scopes[scope] = prev_scope
            prev_scope = scope

    def _get(self, dep: CompilationKey, scope: BaseScope) -> Any:
        registry = self._registries[scope]
        cache = self._cache_by_scope[scope]
        compiled = registry.get_compiled(dep)
        if not compiled:
            parent_scope = self._parent_scopes[scope]
            if parent_scope is None:
                return False
            return self._get(dep, parent_scope)
        return bool(compiled(
            partial(self._get, scope=scope),
            [],
            cache,
            self._context,
            self,
            partial(self._has, scope=scope),
        ))

    def is_active(self, factory: Factory) -> bool:
        marker = factory.provides.as_compilation_key()
        if factory.scope is None:
            error = f"{get_source_name(factory)} as not scope"
            raise DishkaError(error)
        registry = self._registries[factory.scope]
        cache = self._cache_by_scope[factory.scope]
        compiled = registry.get_compiled_activation(marker)
        if not compiled:
            raise RuntimeError
        return bool(compiled(
            partial(self._get, scope=factory.scope),
            [],
            cache,
            self._context,
            self,
            partial(self._has, scope=factory.scope),
        ))

    def _has(self, marker: CompilationKey, scope: BaseScope) -> bool:
        if marker == self._container_key:
            return True
        registry = self._registries[scope]
        cache = self._cache_by_scope[scope]
        compiled = registry.get_compiled_activation(marker)
        if not compiled:
            parent_scope = self._parent_scopes[scope]
            if parent_scope is None:
                return False
            return self._has(marker, parent_scope)
        return bool(compiled(
            partial(self._get, scope=scope),
            [],
            cache,
            self._context,
            self,
            partial(self._has, scope=scope),
        ))

    def export_caches(self) -> dict[BaseScope, dict[Any, object]]:
        return {
            scope: cache.copy()
            for scope, cache in self._cache_by_scope.items()
        }


class StaticEvaluator:
    def __init__(
        self,
        registries: Sequence[Registry],
        context: dict[Any, Any],
        container_key: DependencyKey,
        scopes: type[BaseScope],
        start_scope: BaseScope | None,
    ) -> None:
        self._source_registries = {
            registry.scope: registry for registry in registries
        }
        if start_scope is None:
            start_scope = next(s for s in scopes if not s.skip)
        self.registries: dict[BaseScope, Registry] = {
            registry.scope: static_registry(registry, start_scope)
            for registry in registries
        }
        activation_container = ActivationContainer(
            registries=self.registries,
            container_key=container_key,
            context=context,
        )
        self.activation_container = activation_container

    def _eval_activation(self, factory: Factory) -> None:
        try:
            active = self.activation_container.is_active(factory)
        except StaticEvaluationUnavailable as e:
            logger.debug(
                "Static evaluation for %s is not available: %s",
                factory.provides,
                e,
            )
            return
        if factory.when_override == factory.when_active:
            factory.when_override = BoolMarker(active)
        factory.when_active = BoolMarker(active)

    def evaluate_static(self) -> None:
        for registry in self.registries.values():
            for factory in list(registry.factories.values()):
                self._eval_activation(factory)
        for scope, cache in self.activation_container.export_caches().items():
            self._source_registries[scope].runtime_cache = cache
