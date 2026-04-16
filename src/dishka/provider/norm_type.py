from inspect import ismethod
from typing import Any

from mypyc.ir.ops import Sequence

try:
    from typing import Self
except ImportError:
    Self = None

from dishka.dependency_source import (
    Alias,
    Decorator,
    DependencySource,
    Factory,
)
from dishka.dependency_source.type_replace import replace_type


def is_bound_method(obj: Any) -> bool:
    return ismethod(obj) and bool(obj.__self__)


def _get_self_type(source: Any) -> Any:
    if not ismethod(source):
        return None
    if isinstance(source.__self__, type):
        return source.__self__
    return type(source.__self__)


def normalize_factory_self(self: Any, factory: Factory) -> Factory:
    return factory.replace(
        provides=factory.provides.replace(
            replace_type(factory.provides.type_hint, Self, self),
        ),
        dependencies=[
            dep.replace(
                replace_type(dep.type_hint, Self, self),
            )
            for dep in factory.dependencies
        ],
        kw_dependencies={
            name: dep.replace(
                replace_type(dep.type_hint, Self, self),
            )
            for name, dep in factory.kw_dependencies
        },
    )


def normalize_alias_self(self: Any, alias: Alias) -> Alias:
    return alias.replace(
        source=alias.source.replace(
            replace_type(alias.source.type_hint, Self, self),
        ),
        provides=alias.provides.replace(
            replace_type(alias.provides.type_hint, Self, self),
        ),
    )


def normalize_decorator_self(self: Any, decorator: Decorator) -> Decorator:
    return decorator.replace(
        provides=decorator.provides.replace(
            replace_type(decorator.provides.type_hint, Self, self),
        ),
        factory=normalize_factory_self(self, decorator.factory),
    )


def normalize_sources_self(
    source: Any,
    dep_sources: Sequence[DependencySource],
) -> Sequence[DependencySource]:
    if Self is None or (self := _get_self_type(source)) is None:
        return dep_sources

    res = []
    for dep_source in dep_sources:
        match dep_source:
            case Factory():
                res.append(normalize_factory_self(self, dep_source))
            case Alias():
                res.append(normalize_alias_self(self, dep_source))
            case Decorator():
                res.append(normalize_decorator_self(self, dep_source))
            case _:
                res.append(dep_source)
    return res
