from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Generator,
    Iterable,
    Iterator,
)
from functools import partial
from random import random
from types import NoneType
from typing import (
    Annotated,
    Any,
    ClassVar,
    Final,
    Literal,
    Optional,
    Protocol,
    Union,
    Unpack,
)

import pytest

from dishka import Provider, Scope, alias, decorate, make_container, provide
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import (
    hint_to_dependency_key,
)
from dishka.provider.exceptions import (
    CannotUseProtocolError,
    MissingHintsError,
    MissingReturnHintError,
    NoScopeSetInContextError,
    NoScopeSetInProvideError,
    NotAFactoryError,
    UndefinedTypeAnalysisError,
)
from dishka.provider.make_factory import (
    make_factory,
    provide_all,
    provide_all_on_instance,
    provide_on_instance,
)
from .sample_providers import (
    ClassA,
    async_func_a,
    async_gen_a,
    async_iter_a,
    async_iterator_a,
    sync_func_a,
    sync_gen_a,
    sync_iter_a,
    sync_iterator_a,
)


def test_provider_init():
    class MyProvider(Provider):
        a = alias(source=int, provides=bool)

        @provide(scope=Scope.REQUEST)
        def foo(self, x: object) -> str:
            return f"{x}"

    provider = MyProvider()
    assert len(provider.factories) == 1
    assert len(provider.aliases) == 1


@pytest.mark.parametrize(
    ("source", "provider_type", "is_to_bound"),
    [
        (sync_func_a, FactoryType.FACTORY, True),
        (sync_iter_a, FactoryType.GENERATOR, True),
        (sync_iterator_a, FactoryType.GENERATOR, True),
        (sync_gen_a, FactoryType.GENERATOR, True),
        (async_func_a, FactoryType.ASYNC_FACTORY, True),
        (async_iter_a, FactoryType.ASYNC_GENERATOR, True),
        (async_iterator_a, FactoryType.ASYNC_GENERATOR, True),
        (async_gen_a, FactoryType.ASYNC_GENERATOR, True),
    ],
)
def test_parse_factory(source, provider_type, is_to_bound):
    composite = provide(source, scope=Scope.REQUEST)
    assert len(composite.dependency_sources) == 1
    factory = composite.dependency_sources[0]

    assert factory.provides == hint_to_dependency_key(ClassA)
    assert factory.dependencies == [
        hint_to_dependency_key(Any),
        hint_to_dependency_key(int),
    ]
    assert factory.is_to_bind == is_to_bound
    assert factory.scope == Scope.REQUEST
    assert factory.source == source
    assert factory.type == provider_type


def test_provide_no_scope():
    provider = Provider()
    with pytest.raises(NoScopeSetInProvideError):
        provider.provide(source=int)
    with pytest.raises(NoScopeSetInProvideError):
        provider.provide(A, provides=B)

    def b() -> int:
        return 1

    with pytest.raises(NoScopeSetInProvideError):
        provider.provide(b, provides=B)

    with pytest.raises(NoScopeSetInContextError):
        provider.from_context(b)


def test_parse_factory_invalid_hint():
    def foo(self) -> int:
        yield 1

    with pytest.raises(TypeError):
        provide(foo)


def test_parse_factory_invalid_hint_async():
    async def foo(self) -> int:
        yield 1

    with pytest.raises(TypeError):
        provide(foo)


@pytest.mark.parametrize(
    ("source", "provider_type", "is_to_bound"),
    [
        (ClassA, FactoryType.FACTORY, False),
    ],
)
def test_parse_factory_cls(source, provider_type, is_to_bound):
    factory = make_factory(
        provides=None,
        source=source,
        cache=False,
        scope=Scope.REQUEST,
        is_in_class=False,
        override=False,
    )
    assert factory.provides == hint_to_dependency_key(ClassA)
    assert factory.dependencies == [hint_to_dependency_key(int)]
    assert factory.is_to_bind == is_to_bound
    assert factory.scope == Scope.REQUEST
    assert factory.source == source
    assert factory.type == provider_type


def test_provider_class_scope():
    class MyProvider(Provider):
        scope = Scope.REQUEST

        @provide()
        def foo(self, x: object) -> str:
            return f"{x}"

    provider = MyProvider()
    assert len(provider.factories) == 1
    factory = provider.factories[0]
    assert factory.scope == Scope.REQUEST


def test_provider_instance_scope():
    class MyProvider(Provider):
        @provide()
        def foo(self, x: object) -> str:
            return f"{x}"

    provider = MyProvider(scope=Scope.REQUEST)
    assert len(provider.factories) == 1
    factory = provider.factories[0]
    assert factory.scope == Scope.REQUEST


def test_provider_instance_braces():
    class MyProvider(Provider):
        @provide
        def foo(self, x: object) -> str:
            return f"{x}"

    provider = MyProvider(scope=Scope.REQUEST)
    assert len(provider.factories) == 1
    factory = provider.factories[0]
    assert factory.scope == Scope.REQUEST


def test_self_hint():
    class MyProvider(Provider):
        @provide
        def foo(self: Provider) -> str:
            return "hello"

    provider = MyProvider(scope=Scope.REQUEST)
    assert len(provider.factories) == 1
    factory = provider.factories[0]
    assert not factory.dependencies


def test_staticmethod():
    class MyProvider(Provider):
        @provide
        @staticmethod
        def foo() -> str:
            return "hello"

    provider = MyProvider(scope=Scope.REQUEST)
    assert len(provider.factories) == 1
    factory = provider.factories[0]
    assert not factory.dependencies


def test_classmethod():
    class MyProvider(Provider):
        @provide
        @classmethod
        def foo(cls: type) -> str:
            return "hello"

    provider = MyProvider(scope=Scope.REQUEST)
    assert len(provider.factories) == 1
    factory = provider.factories[0]
    assert not factory.dependencies


class MyCallable:
    def __call__(self: object, param: int) -> str:
        return "hello"


class MyClassCallable:
    @classmethod
    def __call__(cls: object, param: int) -> str:
        return "hello"


class MyStaticCallable:
    @staticmethod
    def __call__(param: int) -> str:
        return "hello"


@pytest.mark.parametrize(
    "cls",
    [MyCallable, MyClassCallable, MyStaticCallable],
)
def test_callable(cls):
    class MyProvider(Provider):
        foo = provide(cls())

    provider = MyProvider(scope=Scope.REQUEST)
    assert len(provider.factories) == 1
    factory = provider.factories[0]
    assert factory.provides == hint_to_dependency_key(str)
    assert factory.dependencies == [hint_to_dependency_key(int)]


def test_provide_as_method():
    provider = Provider(scope=Scope.REQUEST)

    foo = provider.provide(MyCallable())
    assert len(provider.factories) == 1
    assert len(foo.dependency_sources) == 1
    factory = foo.dependency_sources[0]
    assert factory.provides == hint_to_dependency_key(str)
    assert factory.dependencies == [hint_to_dependency_key(int)]

    foo = provider.provide(sync_func_a)
    assert len(foo.dependency_sources) == 1
    factory = foo.dependency_sources[0]
    assert factory.provides == hint_to_dependency_key(ClassA)
    assert factory.dependencies == [
        hint_to_dependency_key(Any),
        hint_to_dependency_key(int),
    ]

    foo = provider.alias(source=int, provides=str)
    assert len(foo.dependency_sources) == 1
    factory = foo.dependency_sources[0]
    assert factory.provides == hint_to_dependency_key(str)
    assert factory.source == hint_to_dependency_key(int)


class OtherClass:
    def method(self) -> str:
        pass


def test_provide_external_method():
    provider = Provider(scope=Scope.REQUEST)
    foo = provider.provide(OtherClass().method)
    assert len(foo.dependency_sources) == 1
    factory = foo.dependency_sources[0]
    assert factory.provides == hint_to_dependency_key(str)
    assert factory.dependencies == []


def test_provide_protocol_impl():
    class MyProto(Protocol):
        pass

    class MyImpl(MyProto):
        pass

    provider = Provider(scope=Scope.REQUEST)
    impl = provider.provide(MyImpl)
    assert len(impl.dependency_sources) == 1
    factory = impl.dependency_sources[0]
    assert factory.provides == hint_to_dependency_key(MyImpl)
    assert factory.dependencies == []


class A:
    pass


class B:
    pass


def test_provide_all_cls():
    class MyProvider(Provider):
        x = provide_all(A, B)

    provider = MyProvider(scope=Scope.APP)
    assert len(provider.factories) == 2
    provides = [f.provides.type_hint for f in provider.factories]
    assert provides == [A, B]


def test_provide_all_instance():
    provider = Provider(scope=Scope.APP)
    provider.provide_all(A, B)
    assert len(provider.factories) == 2
    provides = [f.provides.type_hint for f in provider.factories]
    assert provides == [A, B]


def test_provide_random():
    source = provide(source=random, provides=float)
    assert len(source.dependency_sources) == 1
    assert not source.dependency_sources[0].dependencies


def test_provide_join_provides_cls():
    class MyProvider(Provider):
        x = provide(A) + provide(B)

    provider = MyProvider(scope=Scope.APP)
    assert len(provider.factories) == 2
    provides = [f.provides.type_hint for f in provider.factories]
    assert provides == [A, B]


def test_decorator():
    def sync_func_a(self: ClassA, dep: int) -> ClassA:
        return ClassA(dep)

    provider = Provider(scope=Scope.REQUEST)
    foo = provider.decorate(sync_func_a)
    assert len(foo.dependency_sources) == 1
    factory = foo.dependency_sources[0]
    assert factory.provides == hint_to_dependency_key(ClassA)
    expected_deps = [
        hint_to_dependency_key(ClassA),
        hint_to_dependency_key(int),
    ]
    assert factory.factory.dependencies == expected_deps


def test_invalid_decorator():
    def decorator(self, param: int) -> str:
        return "hello"

    with pytest.raises(ValueError):  # noqa: PT011
        decorate(decorator)


def test_provide_all_as_provider_method():
    def a() -> int:
        return 100

    def b(num: int) -> float:
        return num / 2

    provider = Provider(scope=Scope.APP)
    provider.provide_all(a, b)

    container = make_container(provider)

    hundred = container.get(int)
    assert hundred == 100

    fifty = container.get(float)
    assert fifty == 50.0


def test_provide_all_in_class():
    class MyProvider(Provider):
        scope = Scope.APP

        def a(self) -> int:
            return 100

        def b(self, num: int) -> float:
            return num / 2

        abcd = provide_all(a, b)

    container = make_container(MyProvider())

    hundred = container.get(int)
    assert hundred == 100

    fifty = container.get(float)
    assert fifty == 50.0


make_factory_by_source = partial(
    make_factory,
    provides=None,
    scope=Scope.REQUEST,
    cache=True,
    is_in_class=False,
    override=False,
)


def test_static_method():
    with pytest.raises(TypeError):
        class S1(Provider):

            @provide(scope=Scope.APP)
            @staticmethod
            def s() -> AsyncGenerator[None, None]:
                yield

    with pytest.raises(MissingReturnHintError):
        class S2(Provider):

            @provide(scope=Scope.APP)
            @staticmethod
            def s():
                yield

    with pytest.raises(MissingHintsError):
        class S3(Provider):

            @provide(scope=Scope.APP)
            @staticmethod
            def s(a):
                yield

    with pytest.raises(UndefinedTypeAnalysisError):
        class S4(Provider):

            @provide(scope=Scope.APP)
            @staticmethod
            def s(a: "S5"):  # noqa: F821
                yield


def test_no_hints():
    with pytest.raises(MissingHintsError):
        class C1(Provider):
            @provide(scope=Scope.APP)
            def c(self, a) -> int:
                return 1

    with pytest.raises(MissingReturnHintError):
        class C2(Provider):
            @provide(scope=Scope.APP)
            def c(self, a: int):
                return 1

    def c() -> "C4":  # noqa: F821
        return 1

    with pytest.raises(UndefinedTypeAnalysisError):

        class C3(Provider):
            cp = provide(source=c)


def test_annotated_factory():
    assert make_factory_by_source(source=Annotated[A, "Annotated"])


def test_self():

    with pytest.warns():
        class P(Provider):

            @provide(scope=Scope.APP)
            def a(celph) -> int:  # noqa: N805
                return 1


def foo_aiterable() -> AsyncIterable[NoneType]:
    yield


def foo_aiterator() -> AsyncIterator[int]:
    yield 1


def foo_agen() -> AsyncGenerator[None, None]:
    yield


async def foo_gen() -> Generator[int, None, None]:
    yield 1


async def foo_iterator() -> Iterator[str]:
    yield ""


async def foo_iterable() -> Iterable[float]:
    yield 0


@pytest.mark.parametrize("source", [
    foo_gen, foo_aiterable, foo_aiterator,
    foo_agen, foo_iterable, foo_iterator,
])
def test_factory_error_hints(source):
    with pytest.raises(TypeError):
        make_factory_by_source(source=source)


def test_not_a_factory():
    with pytest.raises(NotAFactoryError):
        make_factory_by_source(source=None)


@pytest.mark.parametrize(
    "provide_func",
    [
        provide,
        provide_all,
        lambda source: provide_on_instance(source=source),
        provide_all_on_instance,
    ],
)
def test_protocol_cannot_be_source_in_provide(provide_func):
    class AProtocol(Protocol): ...

    with pytest.raises(
        CannotUseProtocolError,
        match="Cannot use.*\n.*seems that this is a Protocol.*",
    ):
        class P(Provider):
            p = provide_func(AProtocol)


@pytest.mark.parametrize(
    "type_hint",
    [
        Union[str, int],  # noqa: UP007
        Final[str],
        ClassVar[str],
        Optional[str],  # noqa: UP007
        Unpack[tuple[str]],
        Literal["5"],
    ],
)
def test_generic_alias_not_a_factory(type_hint):
    with pytest.raises(NotAFactoryError):
        make_factory_by_source(source=type_hint)
