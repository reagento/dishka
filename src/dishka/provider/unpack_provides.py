from collections.abc import Sequence
from typing import get_args, get_origin

from dishka.dependency_source import (
    Alias,
    Decorator,
    DependencySource,
    Factory,
)
from dishka.entities.key import DependencyKey
from dishka.entities.provides_marker import ProvideMultiple


def unpack_factory(factory: Factory) -> Sequence[DependencySource]:
    if get_origin(factory.provides.type_hint) is not ProvideMultiple:
        return [factory]

    provides_first, *provides_others = get_args(factory.provides.type_hint)

    res: list[DependencySource] = [
        Alias(
            provides=DependencyKey(provides_other, factory.provides.component),
            source=DependencyKey(provides_first, factory.provides.component),
            cache=factory.cache,
            override=factory.override,
        )
        for provides_other in provides_others
    ]
    res.append(
        Factory(
            dependencies=factory.dependencies,
            kw_dependencies=factory.kw_dependencies,
            type_=factory.type,
            source=factory.source,
            scope=factory.scope,
            is_to_bind=factory.is_to_bind,
            cache=factory.cache,
            override=factory.override,
            provides=DependencyKey(
                provides_first,
                factory.provides.component,
            ),
        ),
    )
    return res


def unpack_decorator(decorator: Decorator) -> Sequence[DependencySource]:
    if get_origin(decorator.provides.type_hint) is not ProvideMultiple:
        return [decorator]

    return [
        Decorator(
            factory=decorator.factory,
            provides=DependencyKey(provides, decorator.provides.component),
        )
        for provides in get_args(decorator.provides.type_hint)
    ]


def unpack_alias(alias: Alias) -> Sequence[DependencySource]:
    if get_origin(alias.provides.type_hint) is not ProvideMultiple:
        return [alias]

    return [
        Alias(
            provides=DependencyKey(provides, alias.provides.component),
            source=alias.source,
            cache=alias.cache,
            override=alias.override,
        )
        for provides in get_args(alias.provides.type_hint)
    ]
