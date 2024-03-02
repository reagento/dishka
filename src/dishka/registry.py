from collections import defaultdict
from typing import Any, NewType, TypeVar, get_args, get_origin

from ._adaptix.type_tools.basic_utils import get_type_vars, is_generic
from .dependency_source import Alias, Factory, from_context
from .entities.component import DEFAULT_COMPONENT
from .entities.key import DependencyKey
from .entities.scope import BaseScope
from .exceptions import (
    CycleDependenciesError,
    NoFactoryError,
)
from .provider import Provider


class Registry:
    __slots__ = ("scope", "factories")

    def __init__(self, scope: BaseScope):
        self.factories: dict[DependencyKey, Factory] = {}
        self.scope = scope

    def add_factory(self, factory: Factory):
        if is_generic(factory.provides.type_hint):
            origin = get_origin(factory.provides.type_hint)
            if origin:
                origin_key = DependencyKey(origin, factory.provides.component)
                self.factories[origin_key] = factory
        self.factories[factory.provides] = factory

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
        params_replacement = dict(zip(
            get_args(factory.provides.type_hint),
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


def make_registries(
        *providers: Provider,
        scopes: type[BaseScope],
        container_type: type,
) -> list[Registry]:
    dep_scopes: dict[DependencyKey, BaseScope] = {}
    alias_sources: dict[DependencyKey, Any] = {}
    aliases: dict[DependencyKey, Alias] = {}
    components = {DEFAULT_COMPONENT}
    for provider in providers:
        component = provider.component
        components.add(component)
        for source in provider.factories:
            provides = source.provides.with_component(component)
            dep_scopes[provides] = source.scope
        for source in provider.aliases:
            provides = source.provides.with_component(component)
            alias_sources[provides] = source.source.with_component(component)
            aliases[provides] = source

    registries: dict[BaseScope, Registry] = {}
    for scope in scopes:
        registry = Registry(scope)
        context_var = from_context(provides=container_type, scope=scope)
        for component in components:
            registry.add_factory(context_var.as_factory(component))
        registries[scope] = registry

    decorator_depth: dict[DependencyKey, int] = defaultdict(int)

    for provider in providers:
        component = provider.component
        for source in provider.factories:
            scope = source.scope
            registries[scope].add_factory(source.with_component(component))
        for source in provider.aliases:
            alias_source = source.source.with_component(component)
            visited_keys = []
            while alias_source not in dep_scopes:
                if alias_source not in alias_sources:
                    e = NoFactoryError(alias_source)
                    for s in visited_keys[::-1]:
                        e.add_path(aliases[s].as_factory("<unknown scope>",
                                                         s.component))
                    e.add_path(source.as_factory("<unknown scope>", component))
                    raise e
                visited_keys.append(alias_source)
                alias_source = alias_sources[alias_source]
                if alias_source in visited_keys:
                    raise CycleDependenciesError([
                        aliases[s].as_factory("<unknown scope>", component)
                        for s in visited_keys
                    ])
            scope = dep_scopes[alias_source]
            source = source.as_factory(scope, component)
            dep_scopes[source.provides] = scope
            registries[scope].add_factory(source)
        for source in provider.decorators:
            provides = source.provides.with_component(component)
            scope = dep_scopes[provides]
            registry = registries[scope]
            undecorated_type = NewType(
                f"{provides.type_hint.__name__}@{decorator_depth[provides]}",
                source.provides,
            )
            decorator_depth[provides] += 1
            old_factory = registry.get_factory(provides)
            old_factory.provides = DependencyKey(
                undecorated_type, old_factory.provides.component,
            )
            registry.add_factory(old_factory)
            source = source.as_factory(
                scope=scope,
                new_dependency=DependencyKey(undecorated_type, None),
                cache=old_factory.cache,
                component=component,
            )
            registries[scope].add_factory(source)
        for source in provider.context_vars:
            scope = source.scope
            registry = registries[scope]
            for component in components:
                registry.add_factory(source.as_factory(component))
    return list(registries.values())
