from typing import Generic, TypeVar

import pytest

from dishka.dependency_source.decorator import is_broader_or_same_type

T = TypeVar("T")


class AGeneric(Generic[T]): ...


class SubAGeneric(AGeneric[T], Generic[T]): ...


class BGeneric(Generic[T]): ...


class C: ...


class SubC(C): ...


class D: ...


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
    ],
)
def test_is_broader_or_same_type(*, first: T, second: T, match: bool):
    assert is_broader_or_same_type(first, second) == match
