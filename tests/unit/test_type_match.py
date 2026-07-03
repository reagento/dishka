import sys
from typing import Generic, Literal, TypeVar

import pytest

from dishka.dependency_source.decorator import (
    get_typevar_replacement,
    is_broader_or_same_type,
)

T = TypeVar("T")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4", bound=str)
T5 = TypeVar("T5", int, str)


class AGeneric(Generic[T]): ...


class SubAGeneric(AGeneric[T], Generic[T]): ...


class BGeneric(Generic[T]): ...


class Multiple(Generic[T, T2, T3]): ...


class C: ...


class SubC(C): ...


class SubC2(C): ...


class D: ...


class CGeneric(Generic[T4]): ...


class DGeneric(Generic[T5]): ...


TC = TypeVar("TC", bound=C)
TCD = TypeVar("TCD", C, D)
TSubCCD = TypeVar("TSubCCD", "C", SubC, D)


@pytest.mark.parametrize(
    ("first", "second", "match"), [
        (C, C, True),
        (C, D, False),
        (TC, C, True),
        (TC, SubC, True),
        (TC, D, False),
        (TSubCCD, TCD, True),
        (AGeneric[C], AGeneric[C], True),
        (AGeneric[TC], AGeneric[C], True),
        (AGeneric[TC], AGeneric[SubC], True),
        (AGeneric[C], BGeneric[C], False),
        (
            Multiple[AGeneric[T], AGeneric[AGeneric[T2]], T3],
            Multiple[AGeneric[int], AGeneric[AGeneric[T]], T2],
            True,
        ),
        (
            Multiple[AGeneric[T], AGeneric[AGeneric[T]], T3],
            Multiple[AGeneric[int], AGeneric[AGeneric[int]], T2],
            True,
        ),
        (
            Multiple[AGeneric[T], AGeneric[AGeneric[T]], T3],
            Multiple[AGeneric[int], AGeneric[AGeneric[str]], T2],
            False,
        ),
        (CGeneric[T4], CGeneric[Literal["a"]], True),
        (CGeneric[T4], CGeneric[Literal[1]], False),
        (DGeneric[T5], DGeneric[Literal[1]], True),
        (DGeneric[T5], DGeneric[Literal["a"]], True),
        (DGeneric[T5], DGeneric[Literal[True]], True),
        (DGeneric[T5], DGeneric[Literal["a", 1]], False),
        # bare (non-alias) union vs a bound TypeVar: broader iff every
        # union member satisfies the bound.
        (TC, SubC | SubC2, True),
        (TC, SubC | D, False),
        # bare union vs a constrained TypeVar: broader iff every member is
        # exactly one of the constraints (invariant, not subclassing).
        (TCD, C | D, True),
        (TCD, C | SubC2, False),
    ],
)
def test_is_broader_or_same_type(*, first: T, second: T, match: bool):
    assert is_broader_or_same_type(first, second) == match


# PEP 695 `type X = ...` aliases (typing.TypeAliasType) only exist on 3.12+.
# Build them via the constructor so this module still parses on 3.10/3.11.
if sys.version_info >= (3, 12):
    from typing import TypeAliasType

    class BoundCGeneric(Generic[TC]): ...

    SingleClassAlias = TypeAliasType("SingleClassAlias", SubC)
    UnionAlias = TypeAliasType("UnionAlias", SubC | SubC2)
    BadUnionAlias = TypeAliasType("BadUnionAlias", SubC | D)
    NestedAlias = TypeAliasType("NestedAlias", UnionAlias)
    ConstraintClassAlias = TypeAliasType("ConstraintClassAlias", C)

    ALIAS_MATCH_CASES = [
        # bound TypeVar vs single-class alias (SubC <: C)
        (TC, SingleClassAlias, True),
        # bound TypeVar vs union alias, every member <: C
        (TC, UnionAlias, True),
        # bound TypeVar vs union alias with a non-subclass member
        (TC, BadUnionAlias, False),
        # alias-to-alias unwraps recursively
        (TC, NestedAlias, True),
        # alias nested in a generic arg
        (BoundCGeneric[TC], BoundCGeneric[UnionAlias], True),
        # constrained TypeVar (C, D) vs single-class alias -> C
        (TCD, ConstraintClassAlias, True),
        # alias nested in a generic arg with a non-subclass member -> False
        (BoundCGeneric[TC], BoundCGeneric[BadUnionAlias], False),
        # alias on the provider side (t1) unwraps at the top level
        (SingleClassAlias, SubC, True),
        # unwrapped alias hits the `t1 == t2` early return
        (C, ConstraintClassAlias, True),
    ]
else:
    ALIAS_MATCH_CASES = []


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="PEP 695 type aliases require Python 3.12+",
)
@pytest.mark.parametrize(("first", "second", "match"), ALIAS_MATCH_CASES)
def test_is_broader_or_same_type_alias(*, first: T, second: T, match: bool):
    assert is_broader_or_same_type(first, second) == match


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="PEP 695 type aliases require Python 3.12+",
)
def test_get_typevar_replacement_unwraps_alias():
    # The substitution dict drives factory compilation, so it must hold the
    # unwrapped concrete type, never the raw TypeAliasType.
    assert get_typevar_replacement(TC, SingleClassAlias) == {TC: SubC}
    assert get_typevar_replacement(TC, UnionAlias) == {TC: SubC | SubC2}
