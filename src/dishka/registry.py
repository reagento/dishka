from collections.abc import Callable
from typing import Any, TypeVar, get_args, get_origin

from ._adaptix.type_tools.fundamentals import get_type_vars
from .container_objects import CompiledFactory
from .dependency_source import (
    Factory,
)
from .dependency_source.type_match import (
    get_typevar_replacement,
    is_broader_or_same_type,
)
from .entities.factory_type import FactoryType
from .entities.key import DependencyKey
from .entities.scope import BaseScope
from .factory_compiler import compile_factory


class Registry:
    __slots__ = (
        "compiled",
        "compiled_async",
        "factories",
        "has_fallback",
        "scope",
    )

    def __init__(self, scope: BaseScope, *, has_fallback: bool) -> None:
        self.scope = scope
        self.factories: dict[DependencyKey, Factory] = {}
        self.compiled: dict[DependencyKey, Callable[..., Any]] = {}
        self.compiled_async: dict[DependencyKey, Callable[..., Any]] = {}
        self.has_fallback = has_fallback

    def add_factory(
            self,
            factory: Factory,
            provides: DependencyKey | None = None,
    ) -> None:
        if provides is None:
            provides = factory.provides
        self.factories[provides] = factory

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
            if origin is type and self.has_fallback:
                return self._get_type_var_factory(dependency)

            origin_key = DependencyKey(origin, dependency.component)
            factory = self.factories.get(origin_key)
            if not factory:
                return None
            if not is_broader_or_same_type(
                    factory.provides.type_hint,
                    dependency.type_hint,
            ):
                return None
            factory = self._specialize_generic(factory, dependency)
            self.factories[dependency] = factory
            return factory

    def _get_type_var_factory(self, dependency: DependencyKey) -> Factory:
        args = get_args(dependency.type_hint)
        if args:
            typevar = args[0]
        else:
            typevar = Any
        return Factory(
            scope=self.scope,
            dependencies=[],
            kw_dependencies={},
            provides=DependencyKey(type[typevar], dependency.component),
            type_=FactoryType.FACTORY,
            is_to_bind=False,
            cache=False,
            override=False,
            source=lambda: typevar,
        )

    def _specialize_generic(
            self, factory: Factory, dependency_key: DependencyKey,
    ) -> Factory:
        params_replacement = get_typevar_replacement(
            factory.provides.type_hint,
            dependency_key.type_hint,
        )
        new_dependencies: list[DependencyKey] = []
        for source_dependency in factory.dependencies:
            hint = source_dependency.type_hint
            if isinstance(hint, TypeVar):
                hint = params_replacement[hint]
            elif get_origin(hint) and (type_vars := get_type_vars(hint)):
                hint = hint[tuple(
                    params_replacement[param]
                    for param in type_vars
                )]
            new_dependencies.append(DependencyKey(
                hint, source_dependency.component,
            ))
        new_kw_dependencies: dict[str, DependencyKey] = {}
        for name, source_dependency in factory.kw_dependencies.items():
            hint = source_dependency.type_hint
            if isinstance(hint, TypeVar):
                hint = params_replacement[hint]
            elif get_origin(hint) and (type_vars := get_type_vars(hint)):
                hint = hint[tuple(
                    params_replacement[param]
                    for param in type_vars
                )]
            new_kw_dependencies[name] = DependencyKey(
                hint, source_dependency.component,
            )
        return Factory(
            source=factory.source,
            provides=dependency_key,
            dependencies=new_dependencies,
            kw_dependencies=new_kw_dependencies,
            is_to_bind=factory.is_to_bind,
            type_=factory.type,
            scope=factory.scope,
            cache=factory.cache,
            override=factory.override,
        )
