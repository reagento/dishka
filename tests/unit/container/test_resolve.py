import math
from typing import Annotated, Protocol, TypeAlias

import pytest

from dishka import (
    Provider,
    Scope,
    from_context,
    make_async_container,
    make_container,
    provide,
)
from dishka.provider import provide_all
from ..sample_providers import (
    A_VALUE,
    ClassA,
    async_func_a,
    async_gen_a,
    async_iter_a,
    sync_func_a,
    sync_gen_a,
    sync_iter_a,
    value_source,
)


@pytest.mark.parametrize(
    ("factory", "closed"),
    [
        (ClassA, False),
        (sync_func_a, False),
        (sync_iter_a, True),
        (sync_gen_a, True),
    ],
)
def test_sync(factory, closed):
    class MyProvider(Provider):
        a = provide(factory, scope=Scope.APP)

        @provide(scope=Scope.APP)
        def get_int(self) -> int:
            return 100

    container = make_container(MyProvider())
    assert container.registry.scope is Scope.APP
    a = container.get(ClassA)
    assert a
    assert a.dep == 100
    container.close()
    assert a.closed == closed


@pytest.mark.parametrize(
    ("factory", "closed"),
    [
        (ClassA, False),
        (sync_func_a, False),
        (sync_iter_a, True),
        (sync_gen_a, True),
        (async_func_a, False),
        (async_iter_a, True),
        (async_gen_a, True),
    ],
)
@pytest.mark.asyncio
async def test_async(factory, closed):
    class MyProvider(Provider):
        a = provide(factory, scope=Scope.APP)

        @provide(scope=Scope.APP)
        def get_int(self) -> int:
            return 100

    container = make_async_container(MyProvider())
    assert container.registry.scope is Scope.APP
    a = await container.get(ClassA)
    assert a
    assert a.dep == 100
    await container.close()
    assert a.closed == closed


def test_2decorators():
    class MyProvider(Provider):
        @provide(scope=Scope.APP)
        @provide(provides=float, scope=Scope.APP)
        def get(self) -> int:
            return 100

    container = make_container(MyProvider())
    assert container.get(float) == 100
    assert container.get(int) == 100


def test_value():
    class MyProvider(Provider):
        factory = value_source

    container = make_container(MyProvider())
    assert container.get(ClassA) is A_VALUE


@pytest.mark.asyncio
async def test_value_async():
    class MyProvider(Provider):
        factory = value_source

    container = make_async_container(MyProvider())
    assert await container.get(ClassA) is A_VALUE


class OtherClass:
    def method(self) -> ClassA:
        return A_VALUE

    @classmethod
    def classmethod(cls) -> ClassA:
        return A_VALUE

    @staticmethod
    def staticmethod() -> ClassA:
        return A_VALUE


@pytest.mark.parametrize("method", [
    OtherClass().method,
    OtherClass().classmethod,
    OtherClass().staticmethod,
])
def test_external_method(method):
    provider = Provider(scope=Scope.APP)
    provider.provide(method)

    container = make_container(provider)
    assert container.get(ClassA) is A_VALUE


def kwarg_factory(a: int, /, b: float, c: complex) -> str:
    return "ok"


def test_kwargs():
    provider = Provider(scope=Scope.APP)
    provider.provide(kwarg_factory)
    provider.provide(lambda: 1, provides=int)
    provider.provide(lambda: 1.0, provides=float)
    provider.provide(lambda: 1j, provides=complex)

    container = make_container(provider)
    assert container.get(str) == "ok"


class _Dep:
    pass


def test_provide_multiple_protocols_before_base():
    class Proto1(Protocol):
        pass

    class Proto2(Protocol):
        pass

    class Base:
        def __init__(self, dep: _Dep) -> None:
            self.dep = dep

    class Multi(Proto1, Proto2, Base):
        pass

    provider = Provider(scope=Scope.APP)
    provider.provide(_Dep)
    provider.provide(Multi)

    container = make_container(provider)
    result = container.get(Multi)
    assert isinstance(result, Multi)
    assert isinstance(result.dep, _Dep)


def test_provide_own_init_overrides_protocol_stub():
    class Proto(Protocol):
        pass

    class Base:
        def __init__(self, dep: _Dep) -> None:
            self.dep = dep

    class Impl(Proto, Base):
        def __init__(self, dep: _Dep) -> None:
            self.own_dep = dep

    provider = Provider(scope=Scope.APP)
    provider.provide(_Dep)
    provider.provide(Impl)

    container = make_container(provider)
    result = container.get(Impl)
    assert isinstance(result, Impl)
    assert isinstance(result.own_dep, _Dep)


def test_provide_protocol_with_explicit_init():
    class ProtoWithInit(Protocol):
        def __init__(self, dep: _Dep) -> None: ...

    class Impl(ProtoWithInit):
        def __init__(self, dep: _Dep) -> None:
            self.dep = dep

    provider = Provider(scope=Scope.APP)
    provider.provide(_Dep)
    provider.provide(Impl)

    container = make_container(provider)
    result = container.get(Impl)
    assert isinstance(result, Impl)
    assert isinstance(result.dep, _Dep)


def test_provide_deep_hierarchy_with_protocol():
    class Proto(Protocol):
        pass

    class GrandBase:
        def __init__(self, dep: _Dep) -> None:
            self.dep = dep

    class Base(GrandBase):
        pass

    class Impl(Proto, Base):
        pass

    provider = Provider(scope=Scope.APP)
    provider.provide(_Dep)
    provider.provide(Impl)

    container = make_container(provider)
    result = container.get(Impl)
    assert isinstance(result, Impl)
    assert isinstance(result.dep, _Dep)


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
    assert math.isclose(fifty, 50.0, abs_tol=1e-9)


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
    assert math.isclose(fifty, 50.0, abs_tol=1e-9)



class ClassX:
    def __init__(self, dep: int, s: str) -> None:
        self.dep = dep
        self.s = s


@pytest.mark.asyncio
async def test_sync_in_async():
    class MyProvider(Provider):
        a = provide(ClassX, scope=Scope.REQUEST)

        @provide(scope=Scope.APP)
        def get_int(self) -> int:
            return 100

        s = from_context(str, scope=Scope.APP)

    container = make_async_container(MyProvider(), context={str: "hello"})
    num = container.get_sync(int)
    assert num == 100

    async with container() as request_container:
        a = request_container.get_sync(ClassX)

    assert a
    assert a.dep == 100
    assert a.s == "hello"


AnnotatedInt: TypeAlias = Annotated[int, "stub"]


def test_get_annotated():
    p = Provider()
    p.provide(lambda: 42, provides=int, scope=Scope.APP)
    c = make_container(p)
    assert c.get(AnnotatedInt) == 42


def test_annotated_provide():
    class P(Provider):
        @provide(scope=Scope.APP)
        def foo(self, x: AnnotatedInt) -> str:
            return str(x)

        @provide(scope=Scope.APP)
        def make_int(self) -> AnnotatedInt:
            return 42

    c = make_container(P())
    assert c.get(str) == "42"

