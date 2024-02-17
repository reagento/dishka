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


def test_provider_class_scope():
    class MyProvider(Provider):
        scope = Scope.REQUEST

        @provide()
        def foo(self, x: bool) -> str:
            return f"{x}"

    provider = MyProvider()
    assert provider.foo.scope == Scope.REQUEST


def test_provider_instance_scope():
    class MyProvider(Provider):
        @provide()
        def foo(self, x: bool) -> str:
            return f"{x}"

    provider = MyProvider(scope=Scope.REQUEST)
    assert provider.foo.scope == Scope.REQUEST


def test_provider_instance_braces():
    class MyProvider(Provider):
        @provide
        def foo(self, x: bool) -> str:
            return f"{x}"

    provider = MyProvider(scope=Scope.REQUEST)
    assert provider.foo.scope == Scope.REQUEST


def test_self_hint():
    class MyProvider(Provider):
        @provide
        def foo(self: Provider) -> str:
            return "hello"

    provider = MyProvider(scope=Scope.REQUEST)
    assert not provider.foo.dependencies


def test_staticmethod():
    class MyProvider(Provider):
        @provide
        @staticmethod
        def foo() -> str:
            return "hello"

    provider = MyProvider(scope=Scope.REQUEST)
    assert not provider.foo.dependencies


def test_classmethod():
    class MyProvider(Provider):
        @provide
        @classmethod
        def foo(cls: type) -> str:
            return "hello"

    provider = MyProvider(scope=Scope.REQUEST)
    assert not provider.foo.dependencies


class MyCallable:
    def __call__(self: object, param: int) -> str:
        return "hello"


def test_callable():
    class MyProvider(Provider):
        foo = provide(MyCallable())

    provider = MyProvider(scope=Scope.REQUEST)
    assert provider.foo.provides == str
    assert provider.foo.dependencies == [int]
