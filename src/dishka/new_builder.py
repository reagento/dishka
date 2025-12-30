from collections import defaultdict
from collections.abc import Sequence
from typing import cast

from .dependency_source import (
    Activation,
    Alias,
    ContextVariable,
    Decorator,
    Factory,
)
from .entities.component import DEFAULT_COMPONENT, Component
from .entities.factory_type import FactoryType
from .entities.key import DependencyKey
from .entities.scope import BaseScope
from .entities.validation_settings import ValidationSettings
from .provider import BaseProvider
from .registry import Registry


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
        self.components: set[Component] = {DEFAULT_COMPONENT}
        self.container_key = container_key
        self.skip_validation = skip_validation
        self.validation_settings = validation_settings
        self.factory_groups: dict[DependencyKey, list[Factory]] = defaultdict(list)

    def _process_alias(self, provider: BaseProvider, src: Alias) -> None:
        factory = src.as_factory(None, provider.component)
        self.factory_groups[factory.provides].append(factory)

    def _process_factory(self, provider: BaseProvider, src: Factory) -> None:
        factory = src.with_component(provider.component)
        self.factory_groups[factory.provides].append(factory)

    def _process_decorator(self, provider: BaseProvider,
                           src: Decorator) -> None:
        provides = src.provides.with_component(provider.component)
        for factory_provides, group in self.factory_groups.items():
            if factory_provides.component != provides.component:
                continue
            if not src.match_type(factory_provides.type_hint):
                continue
            for factory in group:
                # TODO: move original factory if scope changed
                factory.connected_factories.append(src.as_factory(
                    scope=factory.scope,
                    new_dependency=factory.provides,
                    cache=factory.cache,
                    component=factory.provides.component,
                ))

    def _process_context_var(self, provider: BaseProvider,
                             src: ContextVariable) -> None:
        factory = src.as_factory(provider.component)
        self.factory_groups[factory.provides].append(factory)

    def _process_activation(self, provider: BaseProvider,
                            src: Activation) -> None:
        for marker in src.markers:
            factory = src.as_factory(
                provider.scope, provider.component, marker,
            )
            self.factory_groups[factory.provides].append(factory)

    def _fill_factory_scope(self, factory: Factory) -> Factory:
        if factory.scope is not None:
            return factory

        possible_scopes = []
        for dependency in factory.dependencies:
            self._fill_group_scopes(dependency)
            possible_scopes.extend(d.scope for d in self.factory_groups[dependency])
        for dependency in factory.kw_dependencies.values():
            self._fill_group_scopes(dependency)
            possible_scopes.extend(d.scope for d in self.factory_groups[dependency])

        return factory.with_scope(max(possible_scopes))


    def _fill_group_scopes(self, key: DependencyKey):
        group = self.factory_groups[key]
        self.factory_groups[key] = [
            self._fill_factory_scope(factory) for factory in group
        ]

    def _fill_scopes(self):
        for key in self.factory_groups:
            self._fill_group_scopes(key)

    def _unite_selectors(self) -> list[Factory]:
        new_factories: list[Factory] = []
        for provides, group in self.factory_groups.items():
            if len(group) == 1:
                new_factories.append(group[0])
            else:
                factory = Factory(
                    cache=False,
                    scope=group[0].scope,  # TODO check scopes
                    when=None,
                    override=False,
                    provides=provides,
                    is_to_bind=False,
                    dependencies=(),
                    type_=FactoryType.SELECTOR,
                    kw_dependencies={},
                    source=None,
                )
                factory.connected_factories.extend(group)
                new_factories.append(factory)
        return new_factories

    def _make_registries(self, factories: list[Factory]) -> tuple[Registry, ...]:
        registries: dict[BaseScope, Registry] = {}
        has_fallback = True
        for scope in self.scopes:
            registry = Registry(scope, has_fallback=has_fallback)
            registries[scope] = registry
            has_fallback = False
        for factory in factories:
            scope = cast(BaseScope, factory.scope)
            registries[scope].add_factory(factory, factory.provides)
        return tuple(registries.values())

    def build(self) -> tuple[Registry, ...]:
        for provider in self.providers:
            for src in provider.dependency_sources:
                match src:
                    case Alias():
                        self._process_alias(provider, src)
                    case Factory():
                        self._process_factory(provider, src)
                    case Decorator():
                        self._process_decorator(provider, src)
                    case ContextVariable():
                        self._process_context_var(provider, src)
                    case Activation():
                        self._process_activation(provider, src)
                    case _:
                        msg = f"Unsupported dependency source {type(src)}"
                        raise ValueError(msg)

        self._fill_scopes()
        factories = self._unite_selectors()
        registries = self._make_registries(factories)
        return registries
