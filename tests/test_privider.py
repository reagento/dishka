import pytest

from dishka import Provider, Scope, alias, provide
from dishka.provider import ProviderType
from .sample_providers import (
    ClassA, async_func_a, async_gen_a, async_iter_a,
    sync_func_a, sync_gen_a, sync_iter_a,
)


def test_provider_init():
    class MyProvider(Provider):
        a = alias(int, bool)
        b = provide(lambda: False, scope=Scope.APP, dependency=bool)

        @provide(scope=Scope.REQUEST)
        def foo(self, x: bool) -> str:
            return f"{x}"

    provider = MyProvider()
    assert len(provider.dependencies) == 2
    assert len(provider.aliases) == 1


@pytest.mark.parametrize(
    "factory, provider_type, is_to_bound", [
        (ClassA, ProviderType.FACTORY, False),
        (sync_func_a, ProviderType.FACTORY, True),
        (sync_iter_a, ProviderType.GENERATOR, True),
        (sync_gen_a, ProviderType.GENERATOR, True),
        (async_func_a, ProviderType.ASYNC_FACTORY, True),
        (async_iter_a, ProviderType.ASYNC_GENERATOR, True),
        (async_gen_a, ProviderType.ASYNC_GENERATOR, True),
    ]
)
def test_parse_provider(factory, provider_type, is_to_bound):
    dep_provider = provide(factory, scope=Scope.REQUEST)
    assert dep_provider.result_type == ClassA
    assert dep_provider.dependencies == [int]
    assert dep_provider.is_to_bound == is_to_bound
    assert dep_provider.scope == Scope.REQUEST
    assert dep_provider.callable == factory
    assert dep_provider.type == provider_type
