from collections.abc import Sequence

from dishka.entities.key import DependencyKey
from dishka.entities.provides_marker import ProvideMultiple
from .alias import Alias
from .composite import DependencySource
from .decorator import Decorator
from .factory import Factory


def unpack_factory(factory: Factory) -> Sequence[DependencySource]:
    if not isinstance(factory.provides.type_hint, ProvideMultiple):
        return [factory]

    provides_first, *provides_others = factory.provides.type_hint.items

    res: list[DependencySource] = [
        Alias(
            provides=DependencyKey(provides_other, factory.provides.component),
            source=DependencyKey(provides_first, factory.provides.component),
            cache=factory.cache,
        )
        for provides_other in provides_others
    ]
    res.append(Factory(
        dependencies=factory.dependencies,
        type_=factory.type,
        source=factory.source,
        scope=factory.scope,
        provides=DependencyKey(provides_first,
                               factory.provides.component),
        is_to_bind=factory.is_to_bind,
        cache=factory.cache,
    ))
    return res


def unpack_decorator(decorator: Decorator) -> Sequence[DependencySource]:
    if not isinstance(decorator.provides.type_hint, ProvideMultiple):
        return [decorator]

    return [
        Decorator(
            factory=decorator.factory,
            provides=DependencyKey(provides, decorator.provides.component),
        )
        for provides in decorator.provides.type_hint.items
    ]


def unpack_alias(alias: Alias) -> Sequence[DependencySource]:
    if not isinstance(alias.provides.type_hint, ProvideMultiple):
        return [alias]

    return [
        Alias(
            provides=DependencyKey(provides, alias.provides.component),
            source=alias.source,
            cache=alias.cache,
        )
        for provides in alias.provides.type_hint.items
    ]
