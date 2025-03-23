from collections import defaultdict
from collections.abc import Sequence
from typing import Any, TypeVar, cast, get_origin

from ._adaptix.type_tools.basic_utils import is_generic
from .dependency_source import (
    Alias,
    ContextVariable,
    Decorator,
    Factory,
)
from .entities.component import DEFAULT_COMPONENT, Component
from .entities.factory_type import FactoryType
from .entities.key import DependencyKey
from .entities.scope import BaseScope, InvalidScopes, Scope
from .entities.validation_settigs import ValidationSettings
from .exceptions import (
    AliasedFactoryNotFoundError,
    CycleDependenciesError,
    GraphMissingFactoryError,
    ImplicitOverrideDetectedError,
    InvalidGraphError,
    NoFactoryError,
    NothingOverriddenError,
    UnknownScopeError,
)
from .provider import BaseProvider
from .registry import Registry

DECORATED_COMPONENT_PREFIX = "__Dishka_decorate_"


class GraphValidator:
    def __init__(self, registries: Sequence[Registry]) -> None:
        self.registries = registries
        self.path: dict[DependencyKey, Factory] = {}
        self.valid_keys: dict[DependencyKey, bool] = {}

    def _validate_key(
            self, key: DependencyKey, registry_index: int,
    ) -> None:
        if key in self.valid_keys:
            return
        if key in self.path:
            keys = list(self.path)
            factories = list(self.path.values())[keys.index(key):]
            raise CycleDependenciesError(factories)
        for index in range(registry_index + 1):
            registry = self.registries[index]
            factory = registry.get_factory(key)
            if factory:
                self._validate_factory(factory, registry_index)
                return
        raise NoFactoryError(requested=key)

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
            for dep in factory.dependencies:
                # ignore TypeVar parameters
                if not isinstance(dep.type_hint, TypeVar):
                    self._validate_key(dep, registry_index)
            for dep in factory.kw_dependencies.values():
                # ignore TypeVar parameters
                if not isinstance(dep.type_hint, TypeVar):
                    self._validate_key(dep, registry_index)

        except NoFactoryError as e:
            e.add_path(factory)
            raise
        finally:
            self.path.pop(factory.provides)
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
                        e.requested, e.path,
                        self._find_other_scope(e.requested),
                        self._find_other_component(e.requested),
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


class RegistryBuilder:
    def __init__(
            self,
            *,
            scopes: type[BaseScope],
            providers: Sequence[BaseProvider],
            container_key: DependencyKey,
            skip_validation: bool,
            validation_settings: ValidationSettings,
    ) -> None:
        self.scopes = scopes
        self.providers = providers
        self.registries: dict[BaseScope, Registry] = {}
        self.dependency_scopes: dict[DependencyKey, BaseScope] = {}
        self.components: set[Component] = {DEFAULT_COMPONENT}
        self.alias_sources: dict[DependencyKey, Any] = {}
        self.aliases: dict[DependencyKey, Alias] = {}
        self.container_key = container_key
        self.decorator_depth: dict[DependencyKey, int] = defaultdict(int)
        self.skip_validation = skip_validation
        self.validation_settings = validation_settings
        self.processed_factories: dict[DependencyKey, Factory] = {}

    def _collect_components(self) -> None:
        for provider in self.providers:
            self.components.add(provider.component)

    def _collect_provided_scopes(self) -> None:
        for provider in self.providers:
            for factory in provider.factories:
                if not isinstance(factory.scope, self.scopes):
                    raise UnknownScopeError(factory.scope, self.scopes)
                provides = factory.provides.with_component(provider.component)
                self.dependency_scopes[provides] = factory.scope
            for context_var in provider.context_vars:
                for component in self.components:
                    provides = context_var.provides.with_component(component)
                    # typing.cast is applied because the scope
                    # was checked above
                    self.dependency_scopes[provides] = cast(
                        BaseScope, context_var.scope,
                    )

    def _collect_aliases(self) -> None:
        for provider in self.providers:
            component = provider.component
            for alias in provider.aliases:
                provides = alias.provides.with_component(component)
                alias_source = alias.source.with_component(component)
                self.alias_sources[provides] = alias_source
                self.aliases[provides] = alias

    def _init_registries(self) -> None:
        has_fallback = True
        for scope in self.scopes:
            registry = Registry(scope, has_fallback=has_fallback)
            context_var = ContextVariable(
                provides=self.container_key,
                scope=scope,
                override=False,
            )
            for component in self.components:
                registry.add_factory(context_var.as_factory(component))
            self.registries[scope] = registry
            has_fallback = False

    def _process_factory(
            self, provider: BaseProvider, factory: Factory,
    ) -> None:
        factory = factory.with_component(provider.component)
        provides = factory.provides
        if (
            self.validation_settings.nothing_overridden
            and not self.skip_validation
            and factory.override
            and provides not in self.processed_factories
        ):
            raise NothingOverriddenError(factory)

        if (
            self.validation_settings.implicit_override
            and not self.skip_validation
            and not factory.override
            and provides in self.processed_factories
        ):
            raise ImplicitOverrideDetectedError(
                factory,
                self.processed_factories[provides],
            )

        self.processed_factories[provides] = factory
        registry = self.registries[cast(Scope, factory.scope)]
        registry.add_factory(factory)

    def _process_alias(
            self, provider: BaseProvider, alias: Alias,
    ) -> None:
        component = provider.component
        alias_source = alias.source.with_component(component)
        visited_keys: list[DependencyKey] = []
        while alias_source not in self.dependency_scopes:
            if alias_source not in self.alias_sources:
                if self.skip_validation:
                    return
                e = NoFactoryError(alias_source)
                for key in visited_keys[::-1]:
                    e.add_path(self.aliases[key].as_factory(
                        InvalidScopes.UNKNOWN_SCOPE, key.component,
                    ))
                e.add_path(alias.as_factory(
                    InvalidScopes.UNKNOWN_SCOPE, component,
                ))
                raise e
            visited_keys.append(alias_source)
            alias_source = self.alias_sources[alias_source]
            if alias_source in visited_keys:
                if self.skip_validation:
                    return
                raise CycleDependenciesError([
                    self.aliases[s].as_factory(
                        InvalidScopes.UNKNOWN_SCOPE, component,
                    )
                    for s in visited_keys
                ])

        scope = self.dependency_scopes[alias_source]
        registry = self.registries[scope]

        factory = alias.as_factory(scope, component)
        if (
            self.validation_settings.nothing_overridden
            and not self.skip_validation
            and factory.override
            and factory.provides not in self.processed_factories
        ):
            raise NothingOverriddenError(factory)

        if (
            self.validation_settings.implicit_override
            and not self.skip_validation
            and not factory.override
            and factory.provides in self.processed_factories
        ):
            raise ImplicitOverrideDetectedError(
                factory,
                self.processed_factories[factory.provides],
            )

        self.dependency_scopes[factory.provides] = scope
        self.processed_factories[factory.provides] = factory
        registry.add_factory(factory)

    def _process_generic_decorator(
            self, provider: BaseProvider, decorator: Decorator,
    ) -> None:
        found = []
        provides = decorator.provides.with_component(provider.component)
        for registry in self.registries.values():
            for factory in registry.factories.values():
                if factory.provides.component != provides.component:
                    continue
                if factory.type is FactoryType.CONTEXT:
                    continue
                if decorator.match_type(factory.provides.type_hint):
                    found.append((registry, factory))
        if found:
            for registry, factory in found:
                self._decorate_factory(
                    decorator=decorator,
                    registry=registry,
                    old_factory=factory,
                )
        else:
            if not self.validation_settings.nothing_decorated:
                return
            if self.skip_validation:
                return
            raise GraphMissingFactoryError(
                requested=provides,
                path=[decorator.as_factory(
                    scope=InvalidScopes.UNKNOWN_SCOPE,
                    new_dependency=provides,
                    cache=False,
                    component=provider.component,
                )],
            )

    def _process_normal_decorator(
            self, provider: BaseProvider, decorator: Decorator,
    ) -> None:
        provides = decorator.provides.with_component(provider.component)
        if provides not in self.dependency_scopes:
            if not self.validation_settings.nothing_decorated:
                return
            if self.skip_validation:
                return
            raise GraphMissingFactoryError(
                requested=provides,
                path=[decorator.as_factory(
                    scope=InvalidScopes.UNKNOWN_SCOPE,
                    new_dependency=provides,
                    cache=False,
                    component=provider.component,
                )],
            )
        scope = self.dependency_scopes[provides]
        registry = self.registries[scope]
        # factory is expected to be as we already processed
        # it according to dependency_scopes
        old_factory = cast(Factory, registry.get_factory(provides))
        self._decorate_factory(
            decorator=decorator,
            registry=registry,
            old_factory=old_factory,
        )

    def _is_alias_decorated(
        self,
        decorator: Decorator,
        registry: Registry,
        alias: Factory,
    ) -> bool:
        dependency = alias.dependencies[0]
        factory = registry.get_factory(dependency)
        if factory is None:
            raise AliasedFactoryNotFoundError(dependency, alias)
        return factory.source is decorator.factory.source

    def _decorate_factory(
        self,
        decorator: Decorator,
        registry: Registry,
        old_factory: Factory,
    ) -> None:
        provides = old_factory.provides
        if provides.component is None:
            raise ValueError(  # noqa: TRY003
                f"Unexpected empty component for {provides}",
            )
        if (
            old_factory.type is FactoryType.ALIAS
                and self._is_alias_decorated(decorator, registry, old_factory)
        ):
            return
        depth = self.decorator_depth[provides]
        decorated_component = (f"{DECORATED_COMPONENT_PREFIX}{depth}_"
                               f"{provides.component}")
        self.decorator_depth[provides] += 1
        if old_factory is None:
            raise InvalidGraphError(  # noqa: TRY003
                "Cannot apply decorator because there is"
                f"no factory for {provides}",
            )
        if old_factory.type is FactoryType.CONTEXT:
            raise InvalidGraphError(  # noqa: TRY003
                f"Cannot apply decorator to context data {provides}",
            )
        old_factory.provides = DependencyKey(
            old_factory.provides.type_hint, decorated_component,
        )
        new_factory = decorator.as_factory(
            scope=registry.scope,
            new_dependency=old_factory.provides,
            cache=old_factory.cache,
            component=provides.component,
        )
        new_factory.provides = provides
        registry.add_factory(old_factory)
        registry.add_factory(new_factory)

    def _process_context_var(
            self, provider: BaseProvider, context_var: ContextVariable,
    ) -> None:
        if context_var.scope is None:
            raise UnknownScopeError(
                context_var.scope,
                self.scopes,
                extend_message=(
                    "Define it explicitly in Provider or from_context"
                ),
            )
        registry = self.registries[context_var.scope]
        for component in self.components:
            factory = context_var.as_factory(component)
            if (
                self.validation_settings.nothing_overridden
                and not self.skip_validation
                and factory.override
                and factory.provides not in self.processed_factories
            ):
                raise NothingOverriddenError(factory)

            if (
                self.validation_settings.implicit_override
                and not self.skip_validation
                and not factory.override
                and factory.provides in self.processed_factories
            ):
                raise ImplicitOverrideDetectedError(
                    factory,
                    self.processed_factories[factory.provides],
                )
            self.processed_factories[context_var.provides] = factory
            registry.add_factory(factory)

    def build(self) -> tuple[Registry, ...]:
        self._collect_components()
        self._collect_provided_scopes()
        self._collect_aliases()
        self._init_registries()

        for provider in self.providers:
            for factory in provider.factories:
                self._process_factory(provider, factory)
            for alias in provider.aliases:
                self._process_alias(provider, alias)
            for context_var in provider.context_vars:
                self._process_context_var(provider, context_var)
            for decorator in provider.decorators:
                if decorator.is_generic():
                    self._process_generic_decorator(provider, decorator)
                else:
                    self._process_normal_decorator(provider, decorator)
        self._post_process_generic_factories()
        registries = list(self.registries.values())
        if not self.skip_validation:
            GraphValidator(registries).validate()
        return tuple(registries)

    def _post_process_generic_factories(self) -> None:
        found = [
            (registry, factory)
            for registry in self.registries.values()
            for factory in registry.factories.values()
            if is_generic(factory.provides.type_hint)
        ]
        for registry, factory in found:
            origin = get_origin(factory.provides.type_hint)
            origin_key = DependencyKey(origin, factory.provides.component)
            registry.add_factory(factory, origin_key)
