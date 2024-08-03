from abc import ABC
from typing import Any, Generic, Protocol, TypeVar, TypeVarTuple

import pytest

from dishka import Provider, Scope, make_container
from dishka.entities.with_parents import WithParents
from dishka.exceptions import NoFactoryError

T = TypeVar("T")
B = TypeVar("B")
TS = TypeVarTuple("TS")

def test_simple_inheritance() -> None:
    class A1: ...
    class A2(A1): ...
    class A3(A2): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A3(), provides=WithParents[A3])
    container = make_container(provider)
    assert (
        container.get(A3)
        is container.get(A2)
        is container.get(A1)
    )


@pytest.mark.parametrize(
    ("obj", "value"),
    [
        (type("A1", (Protocol,), {}), Protocol),
        (type("A2", (object,), {}), object),
        (type("A3", (ABC,), {}), ABC),
    ],
)
def test_ignore_parent_type(obj: Any, value: Any) -> None:
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: obj(), provides=WithParents[obj])
    container = make_container(provider)

    try:
        container.get(value)
    except NoFactoryError:
        pass
    else:
        raise AssertionError



def test_type_var() -> None:
    class A1(Generic[T]): ...
    class A2(A1[str]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A2(), provides=WithParents[A2])

    container = make_container(provider)

    assert(
        container.get(A2)
        is container.get(A1[str])
    )

def test_type_var_tuple() -> None:
    class A1(Generic[*TS]): ...
    class A2(A1[str, int, type]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A2(), provides=WithParents[A2])

    container = make_container(provider)

    assert (
        container.get(A2)
        is container.get(A1[str, int, type])
    )


def test_type_var_and_type_var_tuple() -> None:
    class A1(Generic[T, *TS]): ...
    class A2(A1[str, int, type]): ...

    class B1(Generic[*TS, T], int): ...
    class B2(B1[int, tuple[str, ...], type]): ...

    class C1(Generic[B, *TS, T]): ...
    class C2(C1[int, type, str, tuple[str, ...]]): ...


    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A2(), provides=WithParents[A2])
    provider.provide(lambda: B2(), provides=WithParents[B2])
    provider.provide(lambda: C2(), provides=WithParents[C2])

    container = make_container(provider)

    assert (
        container.get(A2)
        is container.get(A1[str, int, type])
    )

    assert (
        container.get(B2)
        is container.get(B1[int, tuple[str, ...], type])
        is container.get(int)
    )

    assert (
        container.get(C2)
        is container.get(C1[int, type, str, tuple[str, ...]])
    )

def test_deep_inheritance() -> None:
    class A1(Generic[*TS]): ...
    class A2(A1[*TS], Generic[*TS, T]): ...

    class B1: ...
    class B2(B1): ...
    class B3(B2): ...

    class C1(Generic[T], B3): ...
    class D1(A2[int, type, str], C1[str]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: D1(), provides=WithParents[D1])
    container = make_container(provider)

    assert(
        container.get(D1)
        is container.get(A2[int, type, str])
        is container.get(A1[int, type])
        is container.get(C1[str])
        is container.get(B3)
        is container.get(B2)
        is container.get(B1)
        is container.get(D1)
    )
