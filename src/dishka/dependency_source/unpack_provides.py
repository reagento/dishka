from collections.abc import Sequence
from typing import (
    Union,
)

from dishka._adaptix.type_tools import normalize_type
from dishka.entities.key import DependencyKey
from .alias import Alias
from .composite import DependencySource
from .decorator import Decorator
from .factory import Factory


def unpack_factory(factory: Factory) -> Sequence[DependencySource]:
    provides_normalized = normalize_type(factory.provides.type_hint)
    if provides_normalized.origin is not Union:
        return [factory]

    provides_first, *provides_others = provides_normalized.args

    res = []
    res.append(Factory(
        dependencies=factory.dependencies,
        type_=factory.type,
        source=factory.source,
        scope=factory.scope,
        provides=DependencyKey(provides_first.source,
                               factory.provides.component),
        is_to_bind=factory.is_to_bind,
        cache=factory.cache,
    ))
    for provides_other in provides_others:
        res.append(Alias(
            provides=DependencyKey(provides_other.source,
                                   factory.provides.component),
            source=DependencyKey(provides_first.source,
                                 factory.provides.component),
            cache=factory.cache,
        ))
    return res


def unpack_decorator(decorator: Decorator) -> Sequence[DependencySource]:
    provides_normalized = normalize_type(decorator.provides.type_hint)
    if provides_normalized.origin is not Union:
        return [decorator]

    res = []
    for provides in provides_normalized.args:
        new_decorator = Decorator(decorator.factory)
        new_decorator.provides = DependencyKey(provides.source,
                                               decorator.provides.component)
        res.append(new_decorator)
    return res


def unpack_alias(alias: Alias) -> Sequence[DependencySource]:
    provides_normalized = normalize_type(alias.provides.type_hint)
    if provides_normalized.origin is not Union:
        return [alias]

    res = []
    for provides in provides_normalized.args:
        res.append(Alias(
            provides=DependencyKey(provides.source, alias.provides.component),
            source=alias.source,
            cache=alias.cache,
        ))
    return res
