from typing import Generic, TypeVar

import pytest

from dishka import (
    DEFAULT_COMPONENT,
    DependencyKey,
    Provider,
    Scope,
    alias,
    decorate,
    make_container,
    provide,
)
from dishka.exceptions import CycleDependenciesError, NoFactoryError


class A:
    pass


class A1(A):
    pass


class A2(A1):
    pass


class ADecorator:
    def __init__(self, a: A):
        self.a = a


def test_simple():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

    class DProvider(Provider):
        ad = decorate(ADecorator, provides=A)

    container = make_container(MyProvider(), DProvider())
    a = container.get(A)
    assert isinstance(a, ADecorator)
    assert isinstance(a.a, A)


def test_with_hint():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP, provides=A|None)

    class DProvider(Provider):
        @decorate
        def a(self, a: A|None) -> A|None:
            if a is None:
                return None
            return ADecorator(a)

    container = make_container(MyProvider(), DProvider())
    a = container.get(A|None)
    assert isinstance(a, ADecorator)
    assert isinstance(a.a, A)


def test_decorator():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

    class DProvider(Provider):
        @decorate()
        def foo(self, a: A) -> A:
            return ADecorator(a)

    container = make_container(MyProvider(), DProvider())
    a = container.get(A)
    assert isinstance(a, ADecorator)
    assert isinstance(a.a, A)


def kwarg_decorator(x: int, *, source: A) -> A:
    return ADecorator(source)


def test_kwargs():
    provider = Provider(scope=Scope.APP)
    provider.provide(A)
    provider.decorate(kwarg_decorator)
    provider.provide(lambda: 1, provides=int)

    container = make_container(provider)
    a = container.get(A)
    assert isinstance(a, ADecorator)
    assert isinstance(a.a, A)


def test_decorator_with_provides():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

    class DProvider(Provider):
        @decorate(provides=A)
        def foo(self, a: A):
            return ADecorator(a)

    container = make_container(MyProvider(), DProvider())
    a = container.get(A)
    assert isinstance(a, ADecorator)
    assert isinstance(a.a, A)


def test_alias():
    class MyProvider(Provider):
        a2 = provide(A2, scope=Scope.APP)
        a1 = alias(source=A2, provides=A1)
        a = alias(source=A1, provides=A)

    class DProvider(Provider):
        @decorate
        def decorated(self, a: A1) -> A1:
            return ADecorator(a)

    container = make_container(MyProvider(), DProvider())
    a1 = container.get(A1)
    assert isinstance(a1, ADecorator)
    assert isinstance(a1.a, A2)

    a2 = container.get(A2)
    assert isinstance(a2, A2)
    assert a2 is a1.a

    a = container.get(A)
    assert a is a1


def test_double():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)
        ad = decorate(ADecorator, provides=A)
        ad2 = decorate(ADecorator, provides=A)

    provider = MyProvider()
    assert len(provider.decorators) == 2


def test_double_ok():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

    class DProvider(Provider):
        ad = decorate(ADecorator, provides=A)

    class D2Provider(Provider):
        ad2 = decorate(ADecorator, provides=A)

    container = make_container(MyProvider(), DProvider(), D2Provider())
    a = container.get(A)
    assert isinstance(a, ADecorator)
    assert isinstance(a.a, ADecorator)
    assert isinstance(a.a.a, A)


def test_missing_factory():
    class MyProvider(Provider):
        @decorate
        def foo(self, a: int) -> int:
            return a + 1

    with pytest.raises(NoFactoryError) as e:
        make_container(MyProvider())
    assert e.value.requested == DependencyKey(int, component=DEFAULT_COMPONENT)


def test_expected_decorator():
    class MyProvider(Provider):
        scope = Scope.REQUEST

        @provide(scope=Scope.APP)
        def bar(self) -> A:
            return A()

        @provide(override=True)
        def foo(self, a: A) -> A:
            return a

    with pytest.raises(CycleDependenciesError):
        make_container(MyProvider())


Tint = TypeVar("Tint", bound=int)
T = TypeVar("T")


class GenericA(Generic[T]):
    def __init__(self, value):
        self.value = value


def test_generic_decorator():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide(scope=Scope.APP)
        def bar(self) -> int:
            return 17

        @decorate
        def dec(self, a: Tint) -> Tint:
            return ADecorator(a)

    container = make_container(MyProvider())
    a = container.get(int)
    assert isinstance(a, ADecorator)
    assert a.a == 17


def test_generic_double_decorator():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide(scope=Scope.APP)
        def bar(self) -> int:
            return 17

        @decorate
        def dec(self, a: int) -> int:
            return a+1

        @decorate
        def baz(self, a: Tint) -> Tint:
            return a*2

    container = make_container(MyProvider())
    a = container.get(int)
    assert a == (17+1)*2


def test_generic_decorator_generic_factory():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide(scope=Scope.APP)
        def bar(self, t: type[T]) -> GenericA[T]:
            return GenericA(t())

        @decorate
        def dec(self, a: T) -> T:
            return ADecorator(a)

    container = make_container(MyProvider())
    a = container.get(GenericA[str])
    assert isinstance(a, ADecorator)
    assert isinstance(a.a, GenericA)
    assert a.a.value == ""


def test_decorate_alias():

    class MyProvider(Provider):
        scope = Scope.APP

        @provide(scope=Scope.APP)
        def bar(self) -> int:
            return 17

        baz = alias(source=int, provides=float)

        @decorate
        def dec(self, a: T) -> T:
            return ADecorator(a)

    container = make_container(MyProvider())
    a = container.get(float)
    assert isinstance(a, ADecorator)
    assert a.a == 17
