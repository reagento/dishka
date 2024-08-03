from enum import Enum
from typing import Generic, NamedTuple, Protocol, TypeVar, TypeVarTuple

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
    provider.provide(lambda: 1, provides=WithParents[A3])
    container = make_container(provider)
    assert container.get(A3) == 1
    assert container.get(A2) == 1
    assert container.get(A1) == 1


def test_ignore_parent_type() -> None:
    class A1(Protocol): ...
    class A2(Enum): ...
    class A3(NamedTuple): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: 1, provides=WithParents[A1])
    provider.provide(lambda: 1, provides=WithParents[A2])
    try:
        provider.provide(lambda: 1, provides=WithParents[A3])
    except ValueError:
        pass
    else:
        raise AssertionError
    container = make_container(provider)

    try:
        container.get(Protocol)
    except NoFactoryError:
        pass
    else:
        raise AssertionError

    try:
        container.get(Enum)
    except NoFactoryError:
        pass
    else:
        raise AssertionError



def test_type_var() -> None:
    class A1(Generic[T]): ...
    class A2(A1[str]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: 1, provides=WithParents[A2])

    container = make_container(provider)

    assert container.get(A2) == 1
    assert container.get(A1[str]) == 1


def test_type_var_tuple() -> None:
    class A1(Generic[*TS]): ...
    class A2(A1[str, int, type]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: 1, provides=WithParents[A2])

    container = make_container(provider)

    assert container.get(A2) == 1
    assert container.get(A1[str, int, type]) == 1


def test_type_var_and_type_var_tuple() -> None:
    class A1(Generic[T, *TS]): ...
    class A2(A1[str, int, type]): ...

    class B1(Generic[*TS, T], int): ...
    class B2(B1[int, tuple[str, ...], type]): ...

    class C1(Generic[B, *TS, T]): ...
    class C2(C1[int, type, str, tuple[str, ...]]): ...


    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: 1, provides=WithParents[A2])
    provider.provide(lambda: 1, provides=WithParents[B2])
    provider.provide(lambda: 1, provides=WithParents[C2])

    container = make_container(provider)

    assert container.get(A2) == 1
    assert container.get(A1[str, int, type]) == 1

    assert container.get(B2) == 1
    assert container.get(B1[int, tuple[str, ...], type]) == 1
    assert container.get(int) == 1

    assert container.get(C2) == 1
    assert container.get(C1[int, type, str, tuple[str, ...]]) == 1


def test_deep_inheritance() -> None:
    class A1(Generic[*TS]): ...
    class A2(A1[*TS], Generic[*TS, T]): ...

    class B1: ...
    class B2(B1): ...
    class B3(B2): ...

    class C1(Generic[T], B3): ...
    class D1(A2[int, type, str], C1[str]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: 1, provides=WithParents[D1])
    container = make_container(provider)

    assert container.get(D1) == 1
    assert container.get(A2[int, type, str]) == 1
    assert container.get(A1[int, type]) == 1
    assert container.get(C1[str]) == 1
    assert container.get(B3) == 1
    assert container.get(B2) == 1
    assert container.get(B1) == 1
    assert container.get(D1) == 1
