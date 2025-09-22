from collections import defaultdict
from collections.abc import Sequence
from typing import Any, TypeVar, cast, get_origin

from ._adaptix.type_tools.basic_utils import is_generic
from .dependency_source import (
    Alias,
    ContextVariable,
    Decorator,
    DependencySource,
    Factory,
)
from .entities.activator import ActivationContext
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


ProviderSource = tuple[BaseProvider, DependencySource]


class RegistryBuilder:
    def __init__(
            self,
            *,
            scopes: type[BaseScope],
            providers: Sequence[BaseProvider],
            container_key: DependencyKey,
            skip_validation: bool,
            validation_settings: ValidationSettings,
            root_context: dict[Any, Any] | None,
    ) -> None:
        self.scopes = scopes
        self.providers = providers
        self.all_sources: list[ProviderSource] = []
        self.active_sources: set[ProviderSource] = set()
        self.inactive_sources: set[ProviderSource] = set()
        self.dependency_scopes: dict[DependencyKey, BaseScope] = {}
        self.components: set[Component] = {DEFAULT_COMPONENT}
        self.alias_sources: dict[DependencyKey, Any] = {}
        self.aliases: dict[DependencyKey, Alias] = {}
        self.container_key = container_key
        self.decorator_depth: dict[DependencyKey, int] = defaultdict(int)
        self.skip_validation = skip_validation
        self.validation_settings = validation_settings
        self.processed_factories: dict[DependencyKey, Factory] = {}
        self.root_context = root_context

    def _is_active(
        self,
        provider: BaseProvider,
        source: DependencySource,
        request_stack: list[DependencyKey],
    ) -> bool:
        if (provider, source) in self.active_sources:
            return True
        if (provider, source) in self.inactive_sources:
            return False

        key = source.provides.with_component(provider.component)
        context = ActivationContext(
            container_context=self.root_context,
            container_key=self.container_key,
            key=key,
            builder=self,
            request_stack=[*request_stack, key],
        )
        if ((not source.when or source.when(context)) and
                (not provider.when or provider.when(context))):
            self.active_sources.add((provider, source))
            return True
        self.inactive_sources.add((provider, source))
        return False

    def _collect_sources(self):
        for provider in self.providers:
            for factory in provider.factories:
                self.all_sources.append((provider, factory))
            for alias in provider.aliases:
                self.all_sources.append((provider, alias))
            for context_var in provider.context_vars:
                self.all_sources.append((provider, context_var))
            for decorator in provider.decorators:
                self.all_sources.append((provider, decorator))

    def _filter_active_sources(self):
        self.all_sources = [
            (provider, source)
            for provider, source in self.all_sources
            if self._is_active(provider, source, [])
        ]

    def has_active(
        self,
        key: DependencyKey,
        request_stack: list[DependencyKey],
    ) -> bool:
        for provider, source in self.all_sources:
            src_key = source.provides.with_component(provider.component)
            if (
                src_key==key
                and self._is_active(provider, source, request_stack)
            ):
                return True
        return False

    def _collect_components(self) -> None:
        for provider in self.providers:
            self.components.add(provider.component)

    def _collect_provided_scopes(self) -> None:
        for provider, source in self.all_sources:
            match source:
                case Factory():
                    if not isinstance(source.scope, self.scopes):
                        raise UnknownScopeError(source.scope, self.scopes)
                    key = source.provides.with_component(provider.component)
                    self.dependency_scopes[key] = source.scope
                case ContextVariable():
                    if not isinstance(source.scope, self.scopes):
                        raise UnknownScopeError(source.scope, self.scopes)
                    for component in self.components:
                        key = source.provides.with_component(component)
                        # typing.cast is applied because the scope
                        # was checked above
                        self.dependency_scopes[key] = source.scope
                case Decorator():
                    if not source.scope:
                        continue
                    if not isinstance(source.scope, self.scopes):
                        raise UnknownScopeError(source.scope, self.scopes)
                    key = source.provides.with_component(provider.component)
                    self.dependency_scopes[key] = source.scope



    def _collect_aliases(self) -> None:
        for provider, source in self.all_sources:
            match source:
                case Alias():
                    component = provider.component
                    provides = source.provides.with_component(component)
                    alias_source = source.source.with_component(component)
                    self.alias_sources[provides] = alias_source
                    self.aliases[provides] = source

    def _make_registries(self) -> tuple[Registry, ...]:
        registries: dict[BaseScope, Registry] = {}
        has_fallback = True
        for scope in self.scopes:
            registry = Registry(scope, has_fallback=has_fallback)
            context_var = ContextVariable(
                provides=self.container_key,
                scope=scope,
                override=False,
                # Container have no activation function.
                when=None,
            )
            for component in self.components:
                registry.add_factory(context_var.as_factory(component))
            registries[scope] = registry
            has_fallback = False
        for key, factory in self.processed_factories.items():
            scope = cast(BaseScope, factory.scope)
            registries[scope].add_factory(factory, key)
        return tuple(registries.values())

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

    def _process_generic_decorator(
            self, provider: BaseProvider, decorator: Decorator,
    ) -> None:
        found = []
        provides = decorator.provides.with_component(provider.component)
        for factory in self.processed_factories.values():
            if factory.provides.component != provides.component:
                continue
            if factory.type is FactoryType.CONTEXT:
                continue
            if decorator.match_type(factory.provides.type_hint):
                found.append(factory)
        if found:
            for factory in found:
                self._decorate_factory(
                    decorator=decorator,
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
        old_factory = self.processed_factories[provides]
        self._decorate_factory(
            decorator=decorator,
            old_factory=old_factory,
        )

    def _is_alias_decorated(
        self,
        decorator: Decorator,
        alias: Factory,
    ) -> bool:
        dependency = alias.dependencies[0]
        factory = self.processed_factories.get(dependency)
        if factory is None:
            raise AliasedFactoryNotFoundError(dependency, alias)
        return factory.source is decorator.factory.source

    def _decorate_factory(
        self,
        decorator: Decorator,
        old_factory: Factory,
    ) -> None:
        provides = old_factory.provides
        if provides.component is None:
            raise ValueError(  # noqa: TRY003
                f"Unexpected empty component for {provides}",
            )
        if (
            old_factory.type is FactoryType.ALIAS
                and self._is_alias_decorated(decorator, old_factory)
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
            scope=cast(BaseScope, old_factory.scope),  # all scopes validated
            new_dependency=old_factory.provides,
            cache=old_factory.cache,
            component=provides.component,
        )
        new_factory.provides = provides
        self.processed_factories[old_factory.provides] = old_factory
        self.processed_factories[new_factory.provides] = new_factory

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
            old_factory = self.processed_factories[factory.provides]
            # it's Ok to override context->context with the same params
            if (
                old_factory.type is not FactoryType.CONTEXT or
                old_factory.scope != context_var.scope
            ):
                raise ImplicitOverrideDetectedError(
                    factory,
                    self.processed_factories[factory.provides],
                )
        self.processed_factories[factory.provides] = factory

    def _process_source(
        self,
        provider: BaseProvider,
        source: DependencySource,
    ):
        match source:
            case Factory():
                self._process_factory(provider, source)
            case Alias():
                self._process_alias(provider, source)
            case ContextVariable():
                self._process_context_var(provider, source)
            case Decorator():
                if source.is_generic():
                    self._process_generic_decorator(provider, source)
                else:
                    self._process_normal_decorator(provider, source)
            case _:
                raise TypeError

    def build(self) -> tuple[Registry, ...]:
        self._collect_components()
        self._collect_sources()
        self._filter_active_sources()

        self._collect_provided_scopes()
        self._collect_aliases()

        for provider, source in self.all_sources:
            match source:
                case Factory():
                    key = source.provides.with_component(provider.component)
                    self.dependency_scopes[key] = cast(BaseScope, source.scope)
                case ContextVariable():
                    key = source.provides.with_component(provider.component)
                    self.dependency_scopes[key] = cast(BaseScope, source.scope)

        for provider, source in self.all_sources:
            self._process_source(provider, source)
        self._post_process_generic_factories()

        registries = self._make_registries()
        if not self.skip_validation:
            GraphValidator(registries).validate()
        return registries

    def _post_process_generic_factories(self) -> None:
        found = [
            factory
            for factory in self.processed_factories.values()
            if is_generic(factory.provides.type_hint)
        ]
        for factory in found:
            origin = get_origin(factory.provides.type_hint)
            origin_key = DependencyKey(origin, factory.provides.component)
            self.processed_factories[origin_key] = factory
