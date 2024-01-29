import pytest

from dishka import Provider, Scope, alias, provide
from dishka.dependency_source import FactoryType
from .sample_providers import (
    ClassA,
    async_func_a,
    async_gen_a,
    async_iter_a,
    sync_func_a,
    sync_gen_a,
    sync_iter_a,
)


def test_provider_init():
    class MyProvider(Provider):
        a = alias(source=int, provides=bool)

        @provide(scope=Scope.REQUEST)
        def foo(self, x: bool) -> str:
            return f"{x}"

    provider = MyProvider()
    assert len(provider.factories) == 1
    assert len(provider.aliases) == 1


@pytest.mark.parametrize(
    "source, provider_type, is_to_bound", [
        (ClassA, FactoryType.FACTORY, False),
        (sync_func_a, FactoryType.FACTORY, True),
        (sync_iter_a, FactoryType.GENERATOR, True),
        (sync_gen_a, FactoryType.GENERATOR, True),
        (async_func_a, FactoryType.ASYNC_FACTORY, True),
        (async_iter_a, FactoryType.ASYNC_GENERATOR, True),
        (async_gen_a, FactoryType.ASYNC_GENERATOR, True),
    ],
)
def test_parse_factory(source, provider_type, is_to_bound):
    factory = provide(source, scope=Scope.REQUEST)
    assert factory.provides == ClassA
    assert factory.dependencies == [int]
    assert factory.is_to_bound == is_to_bound
    assert factory.scope == Scope.REQUEST
    assert factory.source == source
    assert factory.type == provider_type
