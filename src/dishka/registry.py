from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any, NewType, TypeVar, get_args, get_origin

from ._adaptix.type_tools.basic_utils import get_type_vars, is_generic
from .container_objects import CompiledFactory
from .dependency_source import (
    Alias,
    ContextVariable,
    Decorator,
    Factory,
    FactoryType,
)
from .entities.component import DEFAULT_COMPONENT, Component
from .entities.key import DependencyKey
from .entities.scope import BaseScope, InvalidScopes
from .exceptions import (
    CycleDependenciesError,
    GraphMissingFactoryError,
    InvalidGraphError,
    NoFactoryError,
    UnknownScopeError,
)
from .factory_compiler import compile_factory
from .provider import BaseProvider


class Registry:
    __slots__ = ("scope", "factories", "compiled", "compiled_async")

    def __init__(self, scope: BaseScope):
        self.factories: dict[DependencyKey, Factory] = {}
        self.compiled: dict[DependencyKey, Callable] = {}
        self.compiled_async: dict[DependencyKey, Callable] = {}
        self.scope = scope

    def add_factory(self, factory: Factory):
        if is_generic(factory.provides.type_hint):
            origin = get_origin(factory.provides.type_hint)
            if origin:
                origin_key = DependencyKey(origin, factory.provides.component)
                self.factories[origin_key] = factory
        self.factories[factory.provides] = factory

    def get_compiled(
            self, dependency: DependencyKey,
    ) -> CompiledFactory | None:
        try:
            return self.compiled[dependency]
        except KeyError:
            factory = self.get_factory(dependency)
            if not factory:
                return None
            compiled = compile_factory(factory=factory, is_async=False)
            self.compiled[dependency] = compiled
            return compiled

    def get_compiled_async(
            self, dependency: DependencyKey,
    ) -> CompiledFactory | None:
        try:
            return self.compiled[dependency]
        except KeyError:
            factory = self.get_factory(dependency)
            if not factory:
                return None
            compiled = compile_factory(factory=factory, is_async=True)
            self.compiled[dependency] = compiled
            return compiled

    def get_factory(self, dependency: DependencyKey) -> Factory | None:
        try:
            return self.factories[dependency]
        except KeyError:
            origin = get_origin(dependency.type_hint)
            if not origin:
                return None
            origin_key = DependencyKey(origin, dependency.component)
            factory = self.factories.get(origin_key)
            if not factory:
                return None

            factory = self._specialize_generic(factory, dependency)
            self.factories[dependency] = factory
            return factory

    def _specialize_generic(
            self, factory: Factory, dependency_key: DependencyKey,
    ) -> Factory:
        dependency = dependency_key.type_hint
        type_var_deps = (
            d.type_hint
            for d in factory.dependencies
            if isinstance(d.type_hint, TypeVar)
        )
        params_replacement = dict(zip(
            type_var_deps,
            get_args(dependency),
            strict=False,
        ))
        new_dependencies: list[DependencyKey] = []
        for source_dependency in factory.dependencies:
            hint = source_dependency.type_hint
            if isinstance(hint, TypeVar):
                hint = params_replacement[hint]
            elif get_origin(hint):
                hint = hint[tuple(
                    params_replacement[param]
                    for param in get_type_vars(hint)
                )]
            new_dependencies.append(DependencyKey(
                hint, source_dependency.component,
            ))
        return Factory(
            source=factory.source,
            provides=dependency_key,
            dependencies=new_dependencies,
            is_to_bind=factory.is_to_bind,
            type_=factory.type,
            scope=factory.scope,
            cache=factory.cache,
        )


class GraphValidator:
    def __init__(self, registries: Sequence[Registry]) -> None:
        self.registries = registries
        self.valid_keys = {}
        self.path = {}

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
    ):
        self.path[factory.provides] = factory
        try:
            for dep in factory.dependencies:
                # ignore TypeVar parameters
                if not isinstance(dep.type_hint, TypeVar):
                    self._validate_key(dep, registry_index)
        except NoFactoryError as e:
            e.add_path(factory)
            raise
        finally:
            self.path.pop(factory.provides)
        self.valid_keys[factory.provides] = True

    def validate(self):
        for registry_index, registry in enumerate(self.registries):
            factories = tuple(registry.factories.values())
            for factory in factories:
                self.path = {}
                try:
                    self._validate_factory(factory, registry_index)
                except NoFactoryError as e:
                    raise GraphMissingFactoryError(
                        e.requested, e.path,
                    ) from None
                except CycleDependenciesError as e:
                    raise e from None


class RegistryBuilder:
    def __init__(
            self,
            *,
            scopes: type[BaseScope],
            providers: Sequence[BaseProvider],
            container_type: type,
            skip_validation: bool,
    ) -> None:
        self.scopes = scopes
        self.providers = providers
        self.registries: dict[BaseScope, Registry] = {}
        self.dependency_scopes: dict[DependencyKey, BaseScope] = {}
        self.components: set[Component] = {DEFAULT_COMPONENT}
        self.alias_sources: dict[DependencyKey, Any] = {}
        self.aliases: dict[DependencyKey, Alias] = {}
        self.container_type = container_type
        self.decorator_depth: dict[DependencyKey, int] = defaultdict(int)
        self.skip_validation = skip_validation

    def _collect_components(self) -> None:
        for provider in self.providers:
            self.components.add(provider.component)

    def _collect_provided_scopes(self) -> None:
        for provider in self.providers:
            for factory in provider.factories:
                if not isinstance(factory.scope, self.scopes):
                    raise UnknownScopeError(
                        f"Scope {factory.scope} is unknown, "
                        f"expected one of {self.scopes}",
                    )
                provides = factory.provides.with_component(provider.component)
                self.dependency_scopes[provides] = factory.scope
            for context_var in provider.context_vars:
                if not isinstance(context_var.scope, self.scopes):
                    raise UnknownScopeError(
                        f"Scope {context_var.scope} is unknown, "
                        f"expected one of {self.scopes}",
                    )
                for component in self.components:
                    provides = context_var.provides.with_component(component)
                    self.dependency_scopes[provides] = context_var.scope

    def _collect_aliases(self) -> None:
        for provider in self.providers:
            component = provider.component
            for alias in provider.aliases:
                provides = alias.provides.with_component(component)
                alias_source = alias.source.with_component(component)
                self.alias_sources[provides] = alias_source
                self.aliases[provides] = alias

    def _init_registries(self) -> None:
        for scope in self.scopes:
            registry = Registry(scope)
            context_var = ContextVariable(
                provides=DependencyKey(self.container_type, DEFAULT_COMPONENT),
                scope=scope,
            )
            for component in self.components:
                registry.add_factory(context_var.as_factory(component))
            self.registries[scope] = registry

    def _process_factory(
            self, provider: BaseProvider, factory: Factory,
    ) -> None:
        registry = self.registries[factory.scope]
        registry.add_factory(factory.with_component(provider.component))

    def _process_alias(
            self, provider: BaseProvider, alias: Alias,
    ) -> None:
        component = provider.component
        alias_source = alias.source.with_component(component)
        visited_keys = []
        while alias_source not in self.dependency_scopes:
            if alias_source not in self.alias_sources:
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
                raise CycleDependenciesError([
                    self.aliases[s].as_factory(
                        InvalidScopes.UNKNOWN_SCOPE, component,
                    )
                    for s in visited_keys
                ])

        scope = self.dependency_scopes[alias_source]
        registry = self.registries[scope]

        factory = alias.as_factory(scope, component)
        self.dependency_scopes[factory.provides] = scope
        registry.add_factory(factory)

    def _process_decorator(
            self, provider: BaseProvider, decorator: Decorator,
    ) -> None:
        provides = decorator.provides.with_component(provider.component)
        if provides not in self.dependency_scopes:
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
        undecorated_type = NewType(
            f"{provides.type_hint.__name__}@{self.decorator_depth[provides]}",
            decorator.provides.type_hint,
        )
        self.decorator_depth[provides] += 1
        old_factory = registry.get_factory(provides)
        if old_factory.type is FactoryType.CONTEXT:
            raise InvalidGraphError(
                f"Cannot apply decorator to context data {provides}",
            )
        old_factory.provides = DependencyKey(
            undecorated_type, old_factory.provides.component,
        )
        new_factory = decorator.as_factory(
            scope=scope,
            new_dependency=DependencyKey(undecorated_type, None),
            cache=old_factory.cache,
            component=provider.component,
        )
        registry.add_factory(old_factory)
        registry.add_factory(new_factory)

    def _process_context_var(
            self, provider: BaseProvider, context_var: ContextVariable,
    ) -> None:
        registry = self.registries[context_var.scope]
        for component in self.components:
            registry.add_factory(context_var.as_factory(component))

    def build(self):
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
                self._process_decorator(provider, decorator)

        registries = list(self.registries.values())
        if not self.skip_validation:
            GraphValidator(registries).validate()
        return tuple(registries)
