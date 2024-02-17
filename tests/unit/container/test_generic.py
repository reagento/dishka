from typing import Generic, TypeVar

import pytest

from dishka import Provider, Scope, make_container, provide

T = TypeVar("T")
U = TypeVar("U")


class Base(Generic[T]):
    def __init__(self, y: T):
        self.y = y


class ReplaceInit(Base[str], Generic[T]):
    def __init__(self, x: T):
        super().__init__("hello")
        self.x = x


class A(Generic[T]):
    def __init__(self, x: T):
        self.x = x


class B(A[U], Generic[U]):
    pass


@pytest.mark.parametrize(
    "cls", [A, B, ReplaceInit],
)
def test_concrete_generic(cls):
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 42

        a = provide(cls[int])

    with make_container(MyProvider()) as container:
        a = container.get(cls[int])
        assert isinstance(a, cls)
        assert a.x == 42


class C(A[int]):
    pass


def test_concrete_child():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 42

        a = provide(C)

    with make_container(MyProvider()) as container:
        a = container.get(C)
        assert isinstance(a, C)
        assert a.x == 42


def test_generic_class():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 42

        a = provide(A)

    with make_container(MyProvider()) as container:
        a = container.get(A[int])
        assert isinstance(a, A)
        assert a.x == 42


def test_generic_func():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 42

        @provide
        def a(self, param: T) -> A[T]:
            return A(param)

    with make_container(MyProvider()) as container:
        a = container.get(A[int])
        assert isinstance(a, A)
        assert a.x == 42
