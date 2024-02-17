from collections import defaultdict
from typing import Any, List, NewType, Type, TypeVar, get_args, get_origin

from ._adaptix.type_tools.basic_utils import get_type_vars, is_generic
from .dependency_source import Factory
from .exceptions import InvalidGraphError
from .provider import Provider
from .scope import BaseScope


class Registry:
    __slots__ = ("scope", "_factories")

    def __init__(self, scope: BaseScope):
        self._factories: dict[Type, Factory] = {}
        self.scope = scope

    def add_factory(self, factory: Factory):
        if is_generic(factory.provides):
            self._factories[get_origin(factory.provides)] = factory
        else:
            self._factories[factory.provides] = factory

    def get_factory(self, dependency: Any) -> Factory | None:
        try:
            return self._factories[dependency]
        except KeyError:
            origin = get_origin(dependency)
            if not origin:
                return None
            factory = self._factories.get(origin)
            if not factory:
                return None

            factory = self._specialize_generic(factory, dependency)
            self._factories[dependency] = factory
            return factory

    def _specialize_generic(
            self, factory: Factory, dependency: Any,
    ) -> Factory:
        params_replacement = dict(zip(
            get_args(factory.provides),
            get_args(dependency),
        ))
        new_dependencies = []
        for source_dependency in factory.dependencies:
            if isinstance(source_dependency, TypeVar):
                source_dependency = params_replacement[source_dependency]
            elif get_origin(source_dependency):
                source_dependency = source_dependency[tuple(
                    params_replacement[param]
                    for param in get_type_vars(source_dependency)
                )]
            new_dependencies.append(source_dependency)
        return Factory(
            source=factory.source,
            provides=dependency,
            dependencies=new_dependencies,
            is_to_bound=factory.is_to_bound,
            type=factory.type,
            scope=factory.scope,
            cache=factory.cache,
        )


def make_registries(
        *providers: Provider, scopes: Type[BaseScope],
) -> List[Registry]:
    dep_scopes: dict[Type, BaseScope] = {}
    alias_sources = {}
    for provider in providers:
        for source in provider.factories:
            dep_scopes[source.provides] = source.scope
        for source in provider.aliases:
            alias_sources[source.provides] = source.source

    registries = {scope: Registry(scope) for scope in scopes}
    decorator_depth: dict[Type, int] = defaultdict(int)

    for provider in providers:
        for source in provider.factories:
            scope = source.scope
            registries[scope].add_factory(source)
        for source in provider.aliases:
            alias_source = source.source
            visited_types = [alias_source]
            while alias_source not in dep_scopes:
                alias_source = alias_sources[alias_source]
                if alias_source in visited_types:
                    raise InvalidGraphError(
                        f"Cycle aliases detected {visited_types}",
                    )
                visited_types.append(alias_source)
            scope = dep_scopes[alias_source]
            dep_scopes[source.provides] = scope
            source = source.as_factory(scope)
            registries[scope].add_factory(source)
        for source in provider.decorators:
            provides = source.provides
            scope = dep_scopes[provides]
            registry = registries[scope]
            undecorated_type = NewType(
                f"{provides.__name__}@{decorator_depth[provides]}",
                source.provides,
            )
            decorator_depth[provides] += 1
            old_factory = registry.get_factory(provides)
            old_factory.provides = undecorated_type
            registry.add_factory(old_factory)
            source = source.as_factory(
                scope, undecorated_type, old_factory.cache,
            )
            registries[scope].add_factory(source)

    return list(registries.values())
