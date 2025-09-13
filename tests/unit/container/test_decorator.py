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
        a = provide(A, scope=Scope.APP, provides=A | None)

    class DProvider(Provider):
        @decorate
        def a(self, a: A | None) -> A | None:
            if a is None:
                return None
            return ADecorator(a)

    container = make_container(MyProvider(), DProvider())
    a = container.get(A | None)
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


class GenericTwoArgs(Generic[T]):
    def __init__(self, value: object, others: object) -> None:
        self.value = value
        self.others = others


def test_generic_multiple_args():
    # https://github.com/reagento/dishka/issues/498
    # one of the args in generic decorator can be concrete generic
    class MyProvider(Provider):
        scope = Scope.APP
        value = provide(lambda self: 42, provides=int)
        others = provide(lambda self: [17], provides=list[int])

        @decorate
        def dec(self, value: Tint, others: list[int]) -> Tint:
            return GenericTwoArgs(value, others)

    container = make_container(MyProvider())
    # we expect double decoration here
    a = container.get(int)
    assert isinstance(a, GenericTwoArgs)
    assert a.value == 42
    assert a.others == [17]


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


def test_decorate_subscope_valid():

    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

        @decorate(scope=Scope.REQUEST)
        def dec(self, a: A) -> A:
            return ADecorator(a)

        @decorate(scope=Scope.ACTION)
        def dec2(self, a: A) -> A:
            return ADecorator(a)

    container = make_container(MyProvider())
    with pytest.raises(NoFactoryError):
        container.get(A)

    with container() as request_container:
        with pytest.raises(NoFactoryError):
            request_container.get(A)
        with request_container() as step_container:
            a1 = step_container.get(A)
        with request_container() as step_container:
            a2 = step_container.get(A)
    assert isinstance(a1, ADecorator)
    assert isinstance(a1.a, ADecorator)
    assert a1 is not a2
    assert a1.a is a2.a

    with container() as request_container:  # noqa: SIM117
        with request_container() as step_container:
            a3 = step_container.get(A)
    assert a1.a is not a3.a
    assert a1.a.a is a2.a.a


def test_decorate_subscope_as_dep():

    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

        @decorate(scope=Scope.REQUEST)
        def dec(self, a: A) -> A:
            return ADecorator(a)

        @provide(scope=Scope.APP)
        def get_int(self, a: A) -> int:
            return 1

    with pytest.raises(NoFactoryError):
        make_container(MyProvider())


def test_decorate_subscope_validate_dep():

    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)

        @decorate(scope=Scope.REQUEST)
        def dec(self, a: A, _: int) -> A:
            return ADecorator(a)

        @provide(scope=Scope.REQUEST)
        def get_int(self) -> int:
            return 1

    assert make_container(MyProvider())


def test_decorate_superscope():

    class MyProvider(Provider):
        a = provide(A, scope=Scope.REQUEST)

        @decorate(scope=Scope.APP)
        def dec(self, a: A) -> A:
            return ADecorator(a)


    with pytest.raises(NoFactoryError):
        make_container(MyProvider())
