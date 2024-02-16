from typing import Generic, TypeVar

import pytest

from dishka import Provider, Scope, make_container, provide

T = TypeVar("T")
U = TypeVar("U")


class A(Generic[T]):
    def __init__(self, x: T):
        self.x = x


class B(A[U], Generic[U]):
    pass


@pytest.mark.parametrize(
    "cls", [A, B],
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
