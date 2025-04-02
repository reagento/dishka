from abc import ABC
from collections.abc import Sequence
from typing import (
    Annotated,
    Any,
    Generic,
    Protocol,
    TypeVar,
)

import pytest

from dishka import (
    DEFAULT_COMPONENT,
    FromComponent,
    Provider,
    Scope,
    make_container,
    provide,
    provide_all,
)
from dishka._adaptix.common import TypeHint
from dishka._adaptix.feature_requirement import HAS_PY_311, HAS_PY_312
from dishka.entities.with_parents import (
    ParentsResolver,
    WithParents,
    is_type_var_tuple,
)
from dishka.exceptions import NoFactoryError

if HAS_PY_311:
    from typing import TypeVarTuple, Unpack

    Ts = TypeVarTuple("TS")  # noqa: PLC0132

if HAS_PY_312:
    from .pep695_new_syntax import (
        A,
        Base,
        Base1,
        Base2,
        Combined,
        D,
        Impl,
        Inner,
        InnerImpl,
        Outer,
        Wrapper,
    )

T = TypeVar("T")
B = TypeVar("B")


@pytest.mark.skipif(
    not HAS_PY_311,
    reason="test for python >= 3.11",
)
def test_is_type_var_tuple() -> None:
    assert is_type_var_tuple(Unpack[Ts])


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
    ("obj", "value", "component"),
    [
        (type("A1", (Protocol,), {}), Protocol, DEFAULT_COMPONENT),
        (type("A2", (object,), {}), object, DEFAULT_COMPONENT),
        (type("A3", (ABC,), {}), ABC, DEFAULT_COMPONENT),
        (type("A3", (ABC,), {}), ABC, "TTT"),
    ],
)
def test_ignore_parent_type(obj: Any, value: Any, component: Any) -> None:
    provider = Provider(scope=Scope.APP, component=component)
    provider.provide(
        source=lambda: obj(),
        provides=Annotated[WithParents[obj], FromComponent(component)],
    )
    container = make_container(provider)

    with pytest.raises(NoFactoryError):
        container.get(value, component=component)


def test_type_var() -> None:
    class A1(Protocol[T]): ...
    class A2(A1[str]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A2(), provides=WithParents[A2])

    container = make_container(provider)

    assert(
        container.get(A2)
        is container.get(A1[str])
    )


@pytest.mark.skipif(
    not HAS_PY_311,
    reason="test for python >= 3.11",
)
def test_type_var_tuple() -> None:
    class A1(Generic[Unpack[Ts]]): ...
    class A2(A1[str, int, type]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A2(), provides=WithParents[A2])

    container = make_container(provider)

    assert (
        container.get(A2)
        is container.get(A1[str, int, type])
    )


if HAS_PY_311:
    class A1(Generic[T, Unpack[Ts]]): ...
    class A2(A1[str, int, type], int): ...

    class B1(Generic[Unpack[Ts], T], int): ...
    class B2(B1[int, tuple[str, ...], type], int): ...

    class C1(Generic[B, Unpack[Ts], T]): ...
    class C2(C1[int, type, str, tuple[str, ...]], int): ...

    params = [
        (A2, A1[str, int, type], int),
        (B2, B1[int, tuple[str, ...], type], int),
        (C2, C1[int, type, str, tuple[str, ...]], int),
    ]
else:
    params = []


@pytest.mark.parametrize(
    ("obj", "val1", "val2"),
    params,
)
@pytest.mark.skipif(
    not HAS_PY_311,
    reason="test for python >= 3.11",
)
def test_type_var_and_type_var_tuple(
    obj: Any,
    val1: Any,
    val2: Any,
) -> None:
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: obj(), provides=WithParents[obj])
    container = make_container(provider)

    assert (
        container.get(obj)
        is container.get(val1)
        is container.get(val2)
    )


def test_deep_inheritance() -> None:
    class A1(Generic[T], float): ...
    class A2(A1[T], Generic[T]): ...

    class B1: ...
    class B2(B1): ...
    class B3(B2): ...

    class C1(Generic[T], B3): ...
    class D1(A2[int], C1[str]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: D1(), provides=WithParents[D1])
    container = make_container(provider)

    assert(
        container.get(D1)
        is container.get(A2[int])
        is container.get(A1[int])
        is container.get(float)
        is container.get(C1[str])
        is container.get(B3)
        is container.get(B2)
        is container.get(B1)
        is container.get(D1)
    )


def test_get_parents_by_generic_alias() -> None:
    class A1(Generic[T], float): ...
    class A2(A1[T], Generic[T]): ...

    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A2(), provides=WithParents[A2[int]])
    container = make_container(provider)

    assert (
        container.get(A2[int])
        is container.get(A1[int])
        is container.get(float)
    )


def test_using_ignoring_type() -> None:
    with pytest.raises(ValueError):  # noqa: PT011
        ParentsResolver().get_parents(object)


def test_ignoring_parent() -> None:
    class A(Generic[T]): ...
    assert ParentsResolver().get_parents(A[int]) == [A[int]]


class TupleGeneric(tuple[T], Generic[T]): ...  # noqa: SLOT001
class SequenceInt(Sequence[int]): ...
class ListAny(list[Any]): ...
class JsonMapping(dict[str, str | int]): ...


@pytest.mark.parametrize(
    ("structure", "result"),
    [
        (TupleGeneric[str], [TupleGeneric[str], tuple[str]]),
        (SequenceInt, [SequenceInt, Sequence[int]]),
        (ListAny, [ListAny, list[Any]]),
        (JsonMapping, [JsonMapping, dict[str, str | int]]),
    ],
)
def test_structures(structure: TypeHint, result: list[TypeHint]) -> None:
    assert ParentsResolver().get_parents(structure) == result


@pytest.mark.skipif(
    not HAS_PY_312,
    reason="PEP 695 syntax requires Python 3.12+",
)
def test_pep695_generic_protocol():
    class MyProvider(Provider):
        scope = Scope.APP
        deps = provide_all(
            WithParents[A[int]],
            WithParents[A[str]],
        )
        one = provide(lambda c: 1, provides=int)
        two = provide(lambda c: "2", provides=str)

    container = make_container(MyProvider())
    assert isinstance(container.get(D[int]).dep, int)
    assert isinstance(container.get(D[str]).dep, str)


@pytest.mark.skipif(
    not HAS_PY_312,
    reason="PEP 695 syntax requires Python 3.12+",
)
def test_pep695_multiple_generics():
    class MyProvider(Provider):
        scope = Scope.APP
        deps = provide_all(
            WithParents[Impl[int, str]],
            WithParents[Impl[str, int]],
        )
        int_ = provide(lambda c: 42, provides=int)
        str_ = provide(lambda c: "text", provides=str)

    container = make_container(MyProvider())
    impl1 = container.get(Base[int, str])
    impl2 = container.get(Base[str, int])

    assert isinstance(impl1.first, int)
    assert isinstance(impl1.second, str)
    assert isinstance(impl2.first, str)
    assert isinstance(impl2.second, int)


@pytest.mark.skipif(
    not HAS_PY_312,
    reason="PEP 695 syntax requires Python 3.12+",
)
def test_pep695_nested_generics():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide(provides=int)
        def provide_int(self) -> int:
            return 100

        @provide(provides=str)
        def provide_str(self) -> str:
            return "nested"

        @provide(provides=Inner[int])
        def provide_inner_int(self) -> Inner[int]:
            return InnerImpl(100)

        @provide(provides=Inner[str])
        def provide_inner_str(self) -> Inner[str]:
            return InnerImpl("nested")

        @provide(provides=Wrapper[int])
        def provide_wrapper_int(self, inner: Inner[int]) -> Wrapper[int]:
            return Wrapper(inner)

        @provide(provides=Wrapper[str])
        def provide_wrapper_str(self, inner: Inner[str]) -> Wrapper[str]:
            return Wrapper(inner)

        @provide(provides=Outer[Inner[int]])
        def provide_outer_int(
                self, wrapper: Wrapper[int],
        ) -> Outer[Inner[int]]:
            return wrapper

        @provide(provides=Outer[Inner[str]])
        def provide_outer_str(
                self, wrapper: Wrapper[str],
        ) -> Outer[Inner[str]]:
            return wrapper

    container = make_container(MyProvider())

    wrapper_int = container.get(Outer[Inner[int]])
    wrapper_str = container.get(Outer[Inner[str]])

    assert isinstance(wrapper_int.value.data, int)
    assert wrapper_int.value.data == 100
    assert isinstance(wrapper_str.value.data, str)
    assert wrapper_str.value.data == "nested"


@pytest.mark.skipif(
    not HAS_PY_312,
    reason="PEP 695 syntax requires Python 3.12+",
)
def test_pep695_multiple_inheritance():
    class MyProvider(Provider):
        scope = Scope.APP
        deps = provide_all(
            WithParents[Combined[int, str]],
            WithParents[Combined[str, int]],
        )
        int_val = provide(lambda c: 7, provides=int)
        str_val = provide(lambda c: "seven", provides=str)

    container = make_container(MyProvider())

    comb1 = container.get(Base1[int])
    comb2 = container.get(Base2[int])
    comb3 = container.get(Base1[str])
    comb4 = container.get(Base2[str])

    assert isinstance(comb1.value1, int)
    assert isinstance(comb2.value2, int)
    assert isinstance(comb3.value1, str)
    assert isinstance(comb4.value2, str)
