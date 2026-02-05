from collections import defaultdict
from collections.abc import Sequence
from typing import cast

from dishka.dependency_source import (
    Activator,
    Alias,
    ContextVariable,
    Decorator,
    Factory,
    FactoryUnionMode,
)
from dishka.entities.component import INTERNAL_COMPONENT_PREFIX, Component
from dishka.entities.factory_type import FactoryData, FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope, InvalidScopes
from dishka.entities.validation_settings import ValidationSettings
from dishka.exception_base import InvalidMarkerError
from dishka.exceptions import (
    ActivatorOverrideError,
    CycleDependenciesError,
    GraphMissingFactoryError,
    UnknownScopeError,
)
from dishka.provider import BaseProvider, ProviderWrapper
from dishka.registry import Registry
from .internal_component_tracker import (
    InternalComponentTracker,
)
from .uniter import (
    CollectionGroupProcessor,
    SelectorGroupProcessor,
)
from .validator import GraphValidator

DECORATED_COMPONENT_PREFIX = f"{INTERNAL_COMPONENT_PREFIX}decorate_"


class GraphBuilder:
    def __init__(
            self,
            scopes: type[BaseScope],
            container_key: DependencyKey,
            skip_validation: bool,
            validation_settings: ValidationSettings,
    ):
        self.scopes = scopes
        self.container_key = container_key
        self.skip_validation = skip_validation
        self.validation_settings = validation_settings
        self.component_tracker = InternalComponentTracker()
        # group processors
        self.selector_group_processor = SelectorGroupProcessor(
            validation_settings=validation_settings,
            skip_validation=skip_validation,
            component_tracker=self.component_tracker,
        )
        self.collection_group_processor = CollectionGroupProcessor(
            validation_settings=validation_settings,
            skip_validation=skip_validation,
            component_tracker=self.component_tracker,
        )

        # registered objects
        self.components: set[Component] = set()
        self.decorator_depth: dict[DependencyKey, int] = {}
        self.factories: dict[DependencyKey, list[Factory]] = defaultdict(list)
        # for multicomponent processing
        self.multicomponent_providers: list[BaseProvider] = []
        self.context_vars: list[ContextVariable] = []
        # for delayed processing
        self.activators: dict[DependencyKey, Activator] = {}
        self.union_modes: dict[DependencyKey, FactoryUnionMode] = {}

    def add_multicomponent_providers(self, *providers: BaseProvider):
        self.multicomponent_providers.extend(providers)
        for component in self.components:
            for provider in providers:
                self._add_provider(ProviderWrapper(component, provider))

    def add_providers(self, *providers: BaseProvider) -> None:
        for provider in providers:
            self._add_provider(provider)

    def _add_provider(self, provider: BaseProvider) -> None:
        component = provider.component
        self._add_component(component)
        for activation in provider.activators:
            self._process_activator(component, activation)
        for factory in provider.factories:
            self._process_factory(component, factory)
        for alias in provider.aliases:
            self._process_alias(component, alias)
        for context_var in provider.context_vars:
            self._process_context_var(component, context_var)
        for union_mode in provider.factory_union_mode:
            self._process_union_mode(component, union_mode)
        for decorator in provider.decorators:
            self._process_decorator(component, decorator)

    def _add_component(self, component: Component) -> None:
        if component in self.components:
            return

        self.components.add(component)
        for provider in self.multicomponent_providers:
            self._add_provider(ProviderWrapper(component, provider))
        for src in self.context_vars:
            factory = src.as_factory(component)
            self.factories[factory.provides].append(factory)

    def _process_alias(self, component: Component, src: Alias) -> None:
        # TODO: process marker alias
        factory = src.as_factory(None, component)
        self.factories[factory.provides].append(factory)

    def _process_factory(self, component: Component, src: Factory) -> None:
        if not isinstance(src.scope, self.scopes):
            raise UnknownScopeError(src.scope, self.scopes)
        factory = src.with_component(component)
        self.factories[factory.provides].append(factory)

    def _process_context_var(
            self,
            component: Component,
            src: ContextVariable,
    ) -> None:
        if not isinstance(src.scope, self.scopes):
            raise UnknownScopeError(src.scope, self.scopes)
        for known_component in self.components:
            factory = src.as_factory(known_component)
            self.factories[factory.provides].append(factory)
        self.context_vars.append(src)

    def _collect_decorating_keys(
            self,
            src: Decorator,
            component: Component,
    ) -> list[DependencyKey]:
        provides = src.provides.with_component(component)
        if src.is_generic():
            found = []
            for factory_provides, group in self.factories.items():
                if (
                        not group or
                        factory_provides.component != provides.component or
                        not src.match_type(factory_provides.type_hint)
                ):
                    continue
                found.append(factory_provides)
            if found:
                return found
        elif provides in self.factories:
            return [provides]

        if (
                self.skip_validation or
                not self.validation_settings.nothing_decorated
        ):
            return []
        raise GraphMissingFactoryError(
            requested=provides,
            path=[src.as_factory(
                scope=InvalidScopes.UNKNOWN_SCOPE,
                new_dependency=provides,
                cache=False,
                component=provides.component,
            )],
        )

    def _is_alias_decorated(self, decorator: Decorator,
                            factory: Factory) -> bool:
        if factory.type is not FactoryType.ALIAS:
            return False
        # TODO: check
        return False

    def _decorate_group(
            self,
            decorator: Decorator,
            provides: DependencyKey,
    ) -> None:
        group_replacement = []
        decorated_groups = {}
        old_group = self.factories[provides]
        for old_factory in old_group:
            if self._is_alias_decorated(decorator, old_factory):
                return

            decorated_provides = self.component_tracker.to_internal_component(
                DECORATED_COMPONENT_PREFIX,
                provides,
            )
            new_factory = old_factory.replace(
                provides=decorated_provides,
                when_active=None,
                when_override=None,
            )
            decorated_groups[decorated_provides] = [new_factory]
            # TODO: handle selection factory
            decorated_factory = decorator.as_factory(
                scope=cast(BaseScope, old_factory.scope),
                new_dependency=decorated_provides,
                cache=old_factory.cache,
                component=provides.component,
            ).replace(
                provides=provides,
                when_active=old_factory.when_active,
                when_override=old_factory.when_override,
                when_component=cast(Component, old_factory.when_component),
            )
            if decorator.when is not None:
                conditional_factory = new_factory.replace(
                    when_override=~decorator.when,
                    when_active=~decorator.when,
                    when_component=provides.component,
                )
                decorated_factory.when_dependencies = [conditional_factory]
            group_replacement.append(decorated_factory)
        self.factories[provides] = group_replacement
        self.factories.update(decorated_groups)

    def _process_decorator(self, component: Component, src: Decorator) -> None:
        if src.scope and not isinstance(src.scope, self.scopes):
            raise UnknownScopeError(src.scope, self.scopes)
        to_decorate = self._collect_decorating_keys(src, component)
        for key in to_decorate:
            self._decorate_group(src, key)

    def _process_union_mode(self, component: Component,
                            src: FactoryUnionMode) -> None:
        src = src.with_component(component)
        self.union_modes[src.source] = src

        factory = src.as_factory()
        if factory:
            self.factories[factory.provides].append(factory)

    def _process_activator(self, component: Component, src: Activator) -> None:
        src = src.with_component(component)
        marker = src.marker or src.marker_type
        if marker is None:
            raise InvalidMarkerError(marker)
        key = DependencyKey(marker, src.factory.when_component)
        if key in self.activators:
            raise ActivatorOverrideError(
                marker,
                [src.factory, self.activators[key].factory],
            )
        self.activators[key] = src

    def _get_factory_union_mode(self, key: DependencyKey) -> FactoryUnionMode:
        if key in self.union_modes:
            return self.union_modes[key]
        return FactoryUnionMode(
            scope=None,
            cache=False,
            collect=False,
            provides=DependencyKey(list[key.type_hint], key.component),
            source=key,
        )

    def _collect_prepared_factories(self):
        factories = []
        for key, factory_group in self.factories.items():
            mode = self._get_factory_union_mode(key)
            if mode.collect:
                factories.extend(
                    self.collection_group_processor.unite(
                        union_mode=mode,
                        provides=key,
                        group=factory_group,
                    ),
                )
            else:
                factories.extend(
                    self.selector_group_processor.unite(
                        union_mode=mode,
                        provides=key,
                        group=factory_group,
                    ),
                )
        return factories

    def _calc_scope(
            self,
            factory: Factory,
            all_factories: dict[DependencyKey, Factory],
            scopes_cache: dict[DependencyKey, BaseScope],
            path: list[FactoryData],
    ) -> BaseScope:
        if factory.scope:
            return factory.scope
        if factory in path:
            raise CycleDependenciesError(path)
        path = path + [factory]
        if factory.provides in scopes_cache:
            return scopes_cache[factory.provides]
        sub_factories: list[FactoryData] = []
        for dep in factory.dependencies:
            if dep in all_factories:
                sub_factories.append(all_factories[dep])
        for dep in factory.kw_dependencies.values():
            if dep in all_factories:
                sub_factories.append(all_factories[dep])
        sub_factories.extend(factory.when_dependencies)

        scopes = [
            self._calc_scope(factory, all_factories, scopes_cache, path)
            for factory in sub_factories
        ]
        scope = max(scopes)
        scopes_cache[factory.provides] = scope
        return scope

    def _make_registries(self, factories: list[Factory]) -> Sequence[Registry]:
        registries: dict[BaseScope, Registry] = {}
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
            registries[scope] = registry
            has_fallback = False

        for factory in factories:
            scope = cast(BaseScope, factory.scope)
            registries[scope].add_factory(factory, factory.provides)
        return tuple(registries.values())

    def build(self) -> Sequence[Registry]:
        factories: dict[DependencyKey, Factory] = {
            f.provides: f for f in self._collect_prepared_factories()
        }

        scope_cache = {}
        fixed_factories: list[Factory] = [
            factory.replace(
                scope=self._calc_scope(factory, factories, scope_cache, []),
            )
            for factory in factories.values()
        ]
        registries = self._make_registries(fixed_factories)
        if not self.skip_validation:
            GraphValidator(registries).validate()
        return registries
