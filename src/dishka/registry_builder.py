from collections import defaultdict
from collections.abc import Sequence
from typing import Any, TypeVar, cast, get_origin

from ._adaptix.type_tools.basic_utils import is_generic
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
from .entities.scope import BaseScope, InvalidScopes
from .entities.validation_settings import ValidationSettings
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
        self,
        key: DependencyKey,
        registry_index: int,
    ) -> None:
        if key in self.valid_keys:
            return
        if key in self.path:
            keys = list(self.path)
            factories = list(self.path.values())[keys.index(key) :]
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
        self.dependency_scopes: dict[DependencyKey, BaseScope] = {}
        self.components: set[Component] = {DEFAULT_COMPONENT}
        self.alias_sources: dict[DependencyKey, Any] = {}
        self.aliases: dict[DependencyKey, Alias] = {}
        self.container_key = container_key
        self.decorator_depth: dict[DependencyKey, int] = defaultdict(int)
        self.skip_validation = skip_validation
        self.validation_settings = validation_settings
        self.processed_factories: dict[DependencyKey, list[Factory]] = {}

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

    def _validate_override(self, factory_list: list[Factory]) -> None:
        if self.skip_validation:
            return

        first_factory, *others = factory_list
        if (
            self.validation_settings.nothing_overridden and
            first_factory.override
        ):
            raise NothingOverriddenError(first_factory)
        if self.validation_settings.implicit_override:
            for other_factory in others:
                if not other_factory.override:
                    raise ImplicitOverrideDetectedError(
                        first_factory,
                        other_factory,
                    )

    def _make_registries(self) -> tuple[Registry, ...]:
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

        for key, factory_list in self.processed_factories.items():
            if not factory_list:
                continue
            self._validate_override(factory_list)
            factory = factory_list[-1]
            scope = cast(BaseScope, factory.scope)
            registries[scope].add_factory(factory, key)
        return tuple(registries.values())

    def _unite_selectors(self) -> list[Factory]:
        new_groups = {}
        for provides, group in self.processed_factories.items():
            if len(group) == 1:
                continue
            when_dependencies = {}
            for factory in group:
                depth = self.decorator_depth[provides]
                self.decorator_depth[provides] += 1
                new_component = (f"{DECORATED_COMPONENT_PREFIX}{depth}_"
                               f"{provides.component}")
                new_provides = DependencyKey(
                    type_hint=provides.type_hint,
                    component=new_component,
                )
                new_factory = factory.replace(provides=new_provides)
                new_groups[new_provides] = [new_factory]
                when_dependencies[new_provides] = DependencyKey(
                    factory.when,
                    factory.provides.component,
                )

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
            factory.when_dependencies = when_dependencies
            self.processed_factories[provides] = [factory]
        self.processed_factories.update(new_groups)

    def _process_activation(self, provider: BaseProvider,
                            src: Activation) -> None:
        for marker in src.markers:
            # TODO scope?
            factory = src.as_factory(
                provider.scope, provider.component, marker,
            )
            lst = self.processed_factories.setdefault(factory.provides, [])
            lst.append(factory)

    def _process_factory(
        self,
        provider: BaseProvider,
        factory: Factory,
    ) -> None:
        factory = factory.with_component(provider.component)
        lst = self.processed_factories.setdefault(factory.provides, [])
        lst.append(factory)

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

        factory = alias.as_factory(scope, component)
        self.dependency_scopes[factory.provides] = scope
        lst = self.processed_factories.setdefault(factory.provides, [])
        lst.append(factory)

    def _process_generic_decorator(
        self,
        provider: BaseProvider,
        decorator: Decorator,
    ) -> None:
        found = []
        provides = decorator.provides.with_component(provider.component)
        for factory_provides in self.processed_factories:
            if factory_provides.component != provides.component:
                continue
            if not decorator.match_type(factory_provides.type_hint):
                continue
            found.append(factory_provides)

        if found:
            for factory_provides in found:
                self._decorate_factory(
                    decorator=decorator,
                    provides=factory_provides,
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
        self._decorate_factory(
            decorator=decorator,
            provides=provides,
        )


    def _is_alias_decorated(
        self,
        decorator: Decorator,
        alias: Factory,
    ) -> bool:
        dependency = alias.dependencies[0]
        factory_list = self.processed_factories.get(dependency)
        if not factory_list:
            raise AliasedFactoryNotFoundError(dependency, alias)
        factory = factory_list[-1]
        return factory.source is decorator.factory.source

    def _decorate_factory(
        self,
        decorator: Decorator,
        provides: DependencyKey,
    ) -> None:
        if provides.component is None:
            raise ValueError(  # noqa: TRY003
                f"Unexpected empty component for {provides}",
            )

        group_replacement = []
        decorated_group = []

        depth = self.decorator_depth[provides]
        self.decorator_depth[provides] += 1
        decorated_component = (f"{DECORATED_COMPONENT_PREFIX}{depth}_"
                               f"{provides.component}")
        decorated_provides = DependencyKey(
            provides.type_hint, decorated_component,
        )

        old_group = self.processed_factories[provides]
        if not old_group:
            raise InvalidGraphError(  # noqa: TRY003
                "Cannot apply decorator because there is"
                f"no factory for {provides}",
            )
        for old_factory in old_group:
            if (
                old_factory.type is FactoryType.ALIAS
                    and self._is_alias_decorated(decorator, old_factory)
            ):
                return

            new_factory = old_factory.replace(provides=decorated_provides)
            decorated_group.append(new_factory)
            group_replacement.append(decorator.as_factory(
                scope=cast(BaseScope, old_factory.scope),
                new_dependency=decorated_provides,
                cache=old_factory.cache,
                component=provides.component,
            ).replace(provides=provides))

        self.processed_factories[provides] = group_replacement
        self.processed_factories[decorated_provides] = decorated_group

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
        factory = context_var.as_factory(provider.component)
        # append context factory to processed list
        lst = self.processed_factories.setdefault(factory.provides, [])
        lst.append(factory)

    def build(self) -> tuple[Registry, ...]:
        self._collect_components()
        self._collect_provided_scopes()
        self._collect_aliases()

        for provider in self.providers:
            for factory in provider.factories:
                self.dependency_scopes[
                    factory.provides.with_component(provider.component)
                ] = cast(BaseScope, factory.scope)

        for provider in self.providers:
            for activation in provider.activations:
                self._process_activation(provider, activation)
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
        self._unite_selectors()
        registries = self._make_registries()
        if not self.skip_validation:
            GraphValidator(registries).validate()
        return registries

    def _post_process_generic_factories(self) -> None:
        found: list[Factory] = []
        for factory_list in self.processed_factories.values():
            for factory in factory_list:
                if is_generic(factory.provides.type_hint):
                    found.append(factory)  # noqa: PERF401
        for factory in found:
            origin = get_origin(factory.provides.type_hint)
            origin_key = DependencyKey(origin, factory.provides.component)
            lst = self.processed_factories.setdefault(origin_key, [])
            lst.append(factory)
